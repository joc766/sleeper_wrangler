package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"sync"
	"syscall"
	"time"

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

func handleEvents(ctx context.Context, db *sql.DB, h *hub.Hub) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		flusher, ok := w.(http.Flusher)
		if !ok {
			http.Error(w, "streaming unsupported", http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "text/event-stream")
		w.Header().Set("Cache-Control", "no-cache")
		w.Header().Set("Connection", "keep-alive")

		subscriber := make(chan hub.Update, 1)
		select {
		case h.Subscribe <- subscriber:
		case <-ctx.Done():
			return
		case <-r.Context().Done():
			return
		}
		defer func() {
			select {
			case h.Unsubscribe <- subscriber:
			case <-ctx.Done():
			}
		}()

		queries := sqlc.New(db)
		latestUpdateText, err := queries.GetLatestProjection(r.Context())
		if err != nil && !errors.Is(err, sql.ErrNoRows) {
			http.Error(w, "error getting latest update", http.StatusInternalServerError)
			return
		}

		if err == nil {
			if _, err := fmt.Fprintf(w, "data: %s\n\n", latestUpdateText); err != nil {
				return
			}
		} else {
			if _, err := fmt.Fprint(w, ": connected; waiting for simulation\n\n"); err != nil {
				return
			}
		}
		flusher.Flush()
		for {
			select {
			case <-ctx.Done():
				return
			case <-r.Context().Done():
				return
			case update, ok := <-subscriber:
				if !ok {
					return
				}
				if err := writeEvent(w, update); err != nil {
					return
				}
				flusher.Flush()
			}
		}

	}
}

func main() {
	if err := run(); err != nil {
		log.Fatal(err)
	}
}

func run() error {
	frontendDir := os.Getenv("FRONTEND_DIR")
	if frontendDir == "" {
		frontendDir = "../frontend"
	}
	if info, err := os.Stat(filepath.Join(frontendDir, "index.html")); err != nil {
		return fmt.Errorf("frontend unavailable; set FRONTEND_DIR to the frontend directory: %w", err)
	} else if info.IsDir() {
		return fmt.Errorf("frontend index.html must be a file")
	}

	db, err := db.Open("/Users/jack/.local/share/sleeper/db.sqlite3")
	if err != nil {
		return err
	}
	defer db.Close()
	subscriberHub := hub.NewHub()

	ctx, cancel := signal.NotifyContext(
		context.Background(),
		os.Interrupt,
		syscall.SIGTERM,
	)
	defer cancel()

	var workers sync.WaitGroup
	workers.Go(func() {
		subscriberHub.Run(ctx)
	})
	workers.Go(func() {
		updater.RunUpdater(ctx, subscriberHub.Updates)
	})

	mux := http.NewServeMux()
	mux.HandleFunc("GET /events", handleEvents(ctx, db, subscriberHub))
	mux.Handle("GET /", http.FileServer(http.Dir(frontendDir)))

	server := &http.Server{
		Addr:    ":8080",
		Handler: mux,
	}

	serverErrors := make(chan error, 1)
	go func() {
		serverErrors <- server.ListenAndServe()
	}()

	var serveErr error
	select {
	case <-ctx.Done():
	case serveErr = <-serverErrors:
	}
	// Restore default signal handling so a second Ctrl+C forces termination.
	cancel()
	log.Print("Shutting down API")
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer shutdownCancel()
	shutdownErr := server.Shutdown(shutdownCtx)
	if shutdownErr != nil {
		_ = server.Close()
	}
	workers.Wait()
	if serveErr != nil && !errors.Is(serveErr, http.ErrServerClosed) {
		return serveErr
	}
	return shutdownErr
}
