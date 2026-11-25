package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"maps"
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

func (cfg AppConfig) writeEvent(ctx context.Context, w io.Writer, update hub.Update) error {
	if cfg.AvatarSource == "roster" {
		rows, err := cfg.Database.QueryContext(ctx, `
			SELECT u.UserName, r.TeamAvatar FROM Roster r JOIN User u ON r.UserID = u.UserID
			WHERE r.LeagueID = (
				SELECT LeagueID FROM League WHERE MasterLeagueID = ?
				ORDER BY Season DESC, LeagueID DESC LIMIT 1
			) AND r.TeamAvatar IS NOT NULL AND r.TeamAvatar != ''`, cfg.MasterLeagueID)
		if err != nil {
			return err
		}
		defer rows.Close()
		avatars := make(map[string]string, len(update.Avatars))
		maps.Copy(avatars, update.Avatars)
		for rows.Next() {
			var username, avatar string
			if err := rows.Scan(&username, &avatar); err != nil {
				return err
			}
			if _, present := update.Projections[username]; present {
				avatars[username] = avatar
			}
		}
		if err := rows.Err(); err != nil {
			return err
		}
		update.Avatars = avatars
	}
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
			var projectionData hub.Update
			if err := json.Unmarshal([]byte(row.Projectiondata), &projectionData); err != nil {
				http.Error(w, "error unmarshalling projection data", http.StatusInternalServerError)
				return
			}
			var week int
			if row.Week.Valid {
				week = int(row.Week.Int64)
			}
			var season string
			if row.Season.Valid {
				season = row.Season.String
			}

			projectionData.Week = week
			projectionData.Season = season
			projectionData.CreatedAt = row.Createdat

			parsedStatuses, err := updater.ParseWeekStatus(row)
			if err != nil {
				http.Error(w, fmt.Sprintf("error marshaling response data: %v", err), http.StatusInternalServerError)
				return
			}
			projectionData.IsComplete = updater.AllGamesComplete(parsedStatuses)
			projectionData.GameCompletion = parsedStatuses
			if err := cfg.writeEvent(r.Context(), w, projectionData); err != nil {
				log.Printf("unable to write initial event: %v", err)
				http.Error(w, "unable to write initial event", http.StatusInternalServerError)
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
				// TODO: get rid of this call; we only need to parse isComplete from the game status
				weekStatus, err := updater.GetWeekStatus(r.Context(), cfg.Queries)
				if err != nil {
					log.Printf("unable to read stored game statuses for event: %v", err)
					continue
				}
				update.IsComplete = weekStatus.IsComplete
				update.GameCompletion = weekStatus.GameCompletion
				if err := cfg.writeEvent(r.Context(), w, update); err != nil {
					log.Printf("unable to write event: %v", err)
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
		// TODO: this call is probably unnecessary, the frontend should be handling if the week is complete or not and sending that information
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

func (cfg AppConfig) handleGetPlayerInfo() http.HandlerFunc {
	type playerInfo struct {
		FullName string `json:"full_name"`
		Position string `json:"position"`
		Team     string `json:"team"`
	}

	return func(w http.ResponseWriter, r *http.Request) {
		playerIDs := r.URL.Query()["player_id"]
		players, err := cfg.Queries.GetPlayerInfo(r.Context(), playerIDs)
		if err != nil {
			http.Error(w, "unable to read player info", http.StatusInternalServerError)
			return
		}

		response := make(map[string]playerInfo, len(players))
		for _, player := range players {
			response[player.Playerid] = playerInfo{
				FullName: player.Fullname,
				Position: player.Position,
				Team:     player.Team.String,
			}
		}

		w.Header().Set("Content-Type", "application/json")
		if err := json.NewEncoder(w).Encode(response); err != nil {
			log.Printf("unable to encode player info response: %v", err)
		}
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
	ProjectionPollInterval time.Duration
	AvatarSource           string
	FrontendDir            string
	PyDir                  string
	Database               *sql.DB
	Queries                *sqlc.Queries
	MasterLeagueID         int
	CountPlayoff           int
	TrackStartSeason       string
	TrackStartWeek         int
}

func loadConfig() (AppConfig, error) {
	var cfg AppConfig
	projectionPollInterval, err := lookupProjectionPollInterval()
	if err != nil {
		return AppConfig{}, err
	}
	cfg.ProjectionPollInterval = projectionPollInterval
	cfg.AvatarSource = os.Getenv("AVATAR_SOURCE")
	switch cfg.AvatarSource {
	case "":
		cfg.AvatarSource = "roster"
	case "roster", "user":
	default:
		return AppConfig{}, fmt.Errorf("AVATAR_SOURCE must be roster or user, got %q", cfg.AvatarSource)
	}

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
		updater.RunUpdater(ctx, cfg.Database, cfg.Queries, subscriberHub.Updates, cfg.ProjectionPollInterval)
	})

	mux := http.NewServeMux()
	mux.HandleFunc("GET /events", cfg.handleEvents(ctx, subscriberHub))
	mux.HandleFunc("GET /loserCounts", cfg.handleGetLoserData(ctx))
	mux.HandleFunc("GET /playerInfo", cfg.handleGetPlayerInfo())
	mux.HandleFunc("GET /chart", func(w http.ResponseWriter, r *http.Request) {
		http.ServeFile(w, r, filepath.Join(cfg.FrontendDir, "chart.html"))
	})
	mux.Handle("GET /", frontendHandler(cfg.FrontendDir))

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
