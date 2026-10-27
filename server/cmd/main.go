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
	"strconv"
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

func (cfg AppConfig) handleEvents(ctx context.Context, h *hub.Hub) http.HandlerFunc {
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

		row, sqlErr := cfg.Queries.GetLatestProjection(r.Context())
		if sqlErr != nil && !errors.Is(sqlErr, sql.ErrNoRows) {
			http.Error(w, "error getting latest update", http.StatusInternalServerError)
			return
		}

		if sqlErr == nil {
			var storedData map[string]json.RawMessage
			if err := json.Unmarshal([]byte(row.Projectiondata), &storedData); err != nil {
				http.Error(w, "error unmarshalling projection data", http.StatusInternalServerError)
				return
			}
			var projectionData hub.Update
			if _, hasEnvelope := storedData["projections"]; hasEnvelope {
				if err := json.Unmarshal([]byte(row.Projectiondata), &projectionData); err != nil {
					http.Error(w, "error unmarshalling projection data", http.StatusInternalServerError)
					return
				}
			} else {
				// Continue to support rows saved before projection metadata was added.
				if err := json.Unmarshal([]byte(row.Projectiondata), &projectionData.Projections); err != nil {
					http.Error(w, "error unmarshalling projection data", http.StatusInternalServerError)
					return
				}
			}

			var week int
			if row.Week.Valid {
				week = int(row.Week.Int64)
			}
			var season string
			if row.Season.Valid {
				season = row.Season.String
			}

			projectionData.CreatedAt = row.Createdat
			projectionData.Week = week
			projectionData.Season = season
			responseData, err := json.Marshal(projectionData)

			if err != nil {
				http.Error(w, "error marshaling response data", http.StatusInternalServerError)
				return
			}
			if _, err := fmt.Fprintf(w, "data: %s\n\n", responseData); err != nil {
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

func (cfg AppConfig) handleGetLoserData(ctx context.Context) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// TODO: need a stable default to fall back to if there's no current data in /LoserProjections (although it will likely fix itself quickly)
		// TODO: We're currently using DisplayWeek everywhere. Probably no value in using the actual Week anyway, since we can know if we need to add 1 for the chart by checking the latest game statuses ourselves anyway
		weekStatus, err := updater.GetWeekStatus(r.Context(), cfg.Queries)
		if err != nil {
			http.Error(w, "unable to read stored game statuses", http.StatusInternalServerError)
			return
		}
		params := sqlc.GetLoserTableParams{
			MasterLeagueID:   int64(cfg.MasterLeagueID),
			CountPlayoff:     sql.NullInt64{Int64: int64(cfg.CountPlayoff), Valid: true},
			TrackStartSeason: cfg.TrackStartSeason,
			TrackStartWeek:   int64(cfg.TrackStartWeek),
			CurrentSeason:    weekStatus.Season,
			CurrentWeek:      weekStatus.Week, // TODO: don't always use DisplayWeek, use normal week
		}
		if weekStatus.IsComplete {
			params.CurrentWeek++
		}
		rows, err := cfg.Queries.GetLoserTable(r.Context(), params)
		if err != nil {
			http.Error(w, fmt.Sprintf("%v", err), http.StatusInternalServerError)
			return
		}

		jsonData, err := json.Marshal(rows)
		if err != nil {
			http.Error(w, fmt.Sprintf("unable to marshal json data: %v", err), http.StatusInternalServerError)
			return
		}
		w.WriteHeader(http.StatusOK)
		w.Header().Set("Content-Type", "application/json")
		w.Write(jsonData)

	}

}

func main() {
	if err := run(); err != nil {
		log.Fatal(err)
	}
}

func lookupFrontendDir() (string, error) {
	frontendDir, ok := os.LookupEnv("FRONTEND_DIR")
	if !ok {
		return "", fmt.Errorf("frontend unavailable; set FRONTEND_DIR to the frontend directory")
	}

	if info, err := os.Stat(filepath.Join(frontendDir, "index.html")); err != nil {
		return "", fmt.Errorf("frontend unavailable; set FRONTEND_DIR to the frontend directory: %w", err)
	} else if info.IsDir() {
		return "", fmt.Errorf("frontend index.html must be a file")
	}
	return frontendDir, nil
}

func openDatabase() (*sql.DB, error) {
	dbPath, ok := os.LookupEnv("DB_PATH")
	if !ok {
		return nil, fmt.Errorf("database unavailable; set DB_PATH to the database path")
	}
	database, err := db.Open(dbPath)
	if err != nil {
		return nil, fmt.Errorf("database unavailable: %w", err)
	}
	return database, nil
}

type AppConfig struct {
	FrontendDir      string
	PyDir            string
	Database         *sql.DB
	Queries          *sqlc.Queries
	MasterLeagueID   int
	CountPlayoff     int
	TrackStartSeason string
	TrackStartWeek   int
}

func loadConfig() (AppConfig, error) {
	var cfg AppConfig

	frontendDir, err := lookupFrontendDir()
	if err != nil {
		return AppConfig{}, err
	}
	cfg.FrontendDir = frontendDir

	database, err := openDatabase()
	if err != nil {
		return AppConfig{}, err
	}
	cfg.Database = database

	cfg.Queries = sqlc.New(database)

	masterLeagueIDStr, ok := os.LookupEnv("MASTER_LEAGUE_ID")
	if !ok {
		return AppConfig{}, fmt.Errorf("must set MASTER_LEAGUE_ID")
	}
	masterLeagueID, err := strconv.Atoi(masterLeagueIDStr)
	if err != nil {
		return AppConfig{}, fmt.Errorf("invalid MASTER_LEAGUE_ID: %v", err)
	}
	cfg.MasterLeagueID = masterLeagueID

	countPlayoffStr, ok := os.LookupEnv("COUNT_PLAYOFF")
	if !ok {
		countPlayoffStr = "0"
	}
	countPlayoff, err := strconv.Atoi(countPlayoffStr)
	if err != nil || countPlayoff > 1 || countPlayoff < 0 {
		return AppConfig{}, fmt.Errorf("invalid COUNT_PLAYOFF_STR (%v): %v", countPlayoffStr, err)
	}
	cfg.CountPlayoff = countPlayoff

	trackStartSeason, ok := os.LookupEnv("TRACK_START_SEASON")
	if !ok || trackStartSeason == "" {
		return AppConfig{}, fmt.Errorf("must set TRACK_START_SEASON")
	}
	cfg.TrackStartSeason = trackStartSeason

	trackStartWeekStr, ok := os.LookupEnv("TRACK_START_WEEK")
	if !ok {
		return AppConfig{}, fmt.Errorf("must set TRACK_START_WEEK")
	}
	trackStartWeek, err := strconv.Atoi(trackStartWeekStr)
	if err != nil || trackStartWeek < 1 {
		return AppConfig{}, fmt.Errorf("invalid TRACK_START_WEEK (%q): must be a positive integer", trackStartWeekStr)
	}
	cfg.TrackStartWeek = trackStartWeek

	return cfg, nil
}

func run() error {
	cfg, err := loadConfig()
	if err != nil {
		if cfg.Database != nil {
			cfg.Database.Close()
		}
		return err
	}
	defer cfg.Database.Close()

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
		updater.RunUpdater(ctx, cfg.Database, cfg.Queries, subscriberHub.Updates)
	})

	mux := http.NewServeMux()
	mux.HandleFunc("GET /events", cfg.handleEvents(ctx, subscriberHub))
	mux.HandleFunc("GET /loserCounts", cfg.handleGetLoserData(ctx))
	mux.HandleFunc("GET /chart", func(w http.ResponseWriter, r *http.Request) {
		http.ServeFile(w, r, filepath.Join(cfg.FrontendDir, "chart.html"))
	})
	mux.Handle("GET /", http.FileServer(http.Dir(cfg.FrontendDir)))

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
