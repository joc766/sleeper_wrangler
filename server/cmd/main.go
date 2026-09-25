package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"

	"github.com/joc766/sleeper/losers/server/internal/db"
	"github.com/joc766/sleeper/losers/server/internal/hub"
	"github.com/joc766/sleeper/losers/server/internal/sqlc"
	"github.com/joc766/sleeper/losers/server/internal/updater"
)

func writeEvent(w io.Writer, update hub.Update) error {
	data, err := json.Marshal(update)
	if err != nil {
		return err
	}

	_, err = fmt.Fprintf(w, "data: %s\n\n", data)
	return err
}

func handleEvents(db *sql.DB, h *hub.Hub) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		flusher, ok := w.(http.Flusher)
		if !ok {
			http.Error(w, "streaming unsupported", http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "text/event-stream")
		w.Header().Set("Cache-Control", "no-cache")
		w.Header().Set("Connection", "keep-alive")

		subscriber := make(chan hub.Update)
		h.Subscribe <- subscriber
		defer func() {
			h.Unsubscribe <- subscriber
		}()

		queries := sqlc.New(db)
		latestUpdateText, err := queries.GetLatestProjection(r.Context())
		if err != nil {
			http.Error(w, "error getting latest update", http.StatusInternalServerError)
			return
		}

		fmt.Fprintf(w, "data: %s\n\n", latestUpdateText)
		flusher.Flush()
		for {
			select {
			case <-r.Context().Done():
			case update := <-subscriber:
				writeEvent(w, update)
				flusher.Flush()
			}
		}

	}
}

func main() {
	db, err := db.Open("/Users/jack/.local/share/sleeper/db.sqlite3")
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()
	subscriberHub := hub.NewHub()

	ctx, cancel := signal.NotifyContext(
		context.Background(),
		os.Interrupt,
		syscall.SIGTERM,
	)
	defer cancel()

	go subscriberHub.Run(ctx)
	go updater.RunUpdater(ctx, subscriberHub.Updates)

	mux := http.NewServeMux()
	mux.HandleFunc("GET /events", handleEvents(db, subscriberHub))

	server := &http.Server{
		Addr:    ":8080",
		Handler: mux,
	}

	log.Fatal(server.ListenAndServe())
}
