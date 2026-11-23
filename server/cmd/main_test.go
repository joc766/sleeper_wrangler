package main

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/joc766/sleeper/losers/server/internal/hub"
	"github.com/joc766/sleeper/losers/server/internal/sqlc"
)

func TestEventAvatarSource(t *testing.T) {
	db, err := sql.Open("sqlite", ":memory:")
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	_, err = db.Exec(`
		CREATE TABLE User (UserID TEXT, UserName TEXT);
		CREATE TABLE League (LeagueID TEXT, Season TEXT, MasterLeagueID INTEGER);
		CREATE TABLE Roster (LeagueID TEXT, UserID TEXT, TeamAvatar TEXT);
		INSERT INTO User VALUES ('1','alice'), ('2','bob');
		INSERT INTO League VALUES ('old','2025',1), ('latest','2026',1), ('other','2027',2);
		INSERT INTO Roster VALUES ('latest','1','team-logo'), ('latest','2',NULL),
			('old','2','old-logo'), ('other','2','other-logo');`)
	if err != nil {
		t.Fatal(err)
	}
	update := hub.Update{
		Projections: map[string]float64{"alice": 0, "bob": 1},
		Avatars:     map[string]string{"alice": "profile-a", "bob": "profile-b"},
	}
	for _, tc := range []struct{ source, alice string }{{"roster", "team-logo"}, {"user", "profile-a"}} {
		cfg := AppConfig{Database: db, MasterLeagueID: 1, AvatarSource: tc.source}
		var event bytes.Buffer
		if err := cfg.writeEvent(context.Background(), &event, update); err != nil {
			t.Fatal(err)
		}
		var got hub.Update
		if err := json.Unmarshal(bytes.TrimPrefix(event.Bytes(), []byte("data: ")), &got); err != nil {
			t.Fatal(err)
		}
		if got.Avatars["alice"] != tc.alice || got.Avatars["bob"] != "profile-b" {
			t.Errorf("%s avatars: %v", tc.source, got.Avatars)
		}
	}
}

type flushRecorder struct {
	*httptest.ResponseRecorder
	flushed chan struct{}
}

func (w *flushRecorder) Flush() {
	w.ResponseRecorder.Flush()
	select {
	case w.flushed <- struct{}{}:
	default:
	}
}

func TestEventsCancellation(t *testing.T) {
	for _, shutdown := range []bool{false, true} {
		name := "client disconnect"
		if shutdown {
			name = "application shutdown"
		}
		t.Run(name, func(t *testing.T) {
			database, err := sql.Open("sqlite", ":memory:")
			if err != nil {
				t.Fatal(err)
			}
			defer database.Close()
			if _, err := database.Exec("CREATE TABLE LoserProjections (LoserProjectionID INTEGER PRIMARY KEY, ProjectionData TEXT, CreatedAt TEXT, Gamestatus TEXT, Week INTEGER, Season TEXT)"); err != nil {
				t.Fatal(err)
			}
			queries := sqlc.New(database)
			cfg := AppConfig{Queries: queries}
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			h := hub.NewHub()
			go h.Run(ctx)
			requestCtx, disconnect := context.WithCancel(context.Background())
			defer disconnect()
			r := httptest.NewRequest("GET", "/events", nil).WithContext(requestCtx)
			w := &flushRecorder{httptest.NewRecorder(), make(chan struct{}, 1)}
			done := make(chan struct{})
			go func() {
				cfg.handleEvents(ctx, h)(w, r)
				close(done)
			}()
			select {
			case <-w.flushed:
			case <-time.After(2 * time.Second):
				t.Fatal("SSE connection did not open with an empty projections table")
			}
			if shutdown {
				cancel()
			} else {
				disconnect()
			}
			select {
			case <-done:
			case <-time.After(2 * time.Second):
				t.Fatal("SSE handler did not exit after cancellation")
			}
		})
	}
}
