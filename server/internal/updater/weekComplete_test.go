package updater

import (
	"context"
	"database/sql"
	"testing"

	"github.com/joc766/sleeper/losers/server/internal/sqlc"
	_ "modernc.org/sqlite"
)

func TestStoredWeekComplete(t *testing.T) {
	db, err := sql.Open("sqlite", ":memory:")
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	db.SetMaxOpenConns(1)
	_, err = db.Exec(`CREATE TABLE LoserProjections (LoserProjectionID INTEGER PRIMARY KEY, ProjectionData TEXT, CreatedAt TEXT, GameStatus, Week INTEGER, Season TEXT)`)
	if err != nil {
		t.Fatal(err)
	}
	queries := sqlc.New(db)
	if got, err := IsWeekComplete(context.Background(), queries, "2026", 7); err != nil || got {
		t.Fatalf("empty database: got %v, %v", got, err)
	}
	for _, tt := range []struct {
		name     string
		season   any
		week     any
		statuses any
		want     bool
		wantErr  bool
	}{
		{"complete", "2026", 7, `{"DAL":1,"WAS":1}`, true, false},
		{"previous week", "2026", 6, `{"DAL":1}`, false, false},
		{"previous season", "2025", 7, `{"DAL":1}`, false, false},
		{"missing season", nil, 7, `{"DAL":1}`, false, false},
		{"missing week", "2026", nil, `{"DAL":1}`, false, false},
		{"missing statuses", "2026", 7, nil, false, false},
		{"empty statuses", "2026", 7, `{}`, false, false},
		{"in progress", "2026", 7, `{"DAL":0.5}`, false, false},
		{"blob", "2026", 7, []byte(`{"DAL":1}`), true, false},
		{"invalid JSON", "2026", 7, `broken`, false, true},
	} {
		t.Run(tt.name, func(t *testing.T) {
			_, err := db.Exec(`INSERT INTO LoserProjections (ProjectionData, CreatedAt, GameStatus, Week, Season) VALUES ('{}', '', ?, ?, ?)`, tt.statuses, tt.week, tt.season)
			if err != nil {
				t.Fatal(err)
			}
			got, err := IsWeekComplete(context.Background(), queries, "2026", 7)
			if got != tt.want || (err != nil) != tt.wantErr {
				t.Fatalf("got %v, %v; want complete=%v, error=%v", got, err, tt.want, tt.wantErr)
			}
		})
	}
}

func TestAllGamesComplete(t *testing.T) {
	for _, tt := range []struct {
		name     string
		statuses map[string]float64
		want     bool
	}{
		{"empty", nil, false},
		{"finished", map[string]float64{"WAS": 1, "DAL": 1}, true},
		{"in progress", map[string]float64{"WAS": 1, "DAL": 0.5}, false},
		{"not started", map[string]float64{"WAS": 1, "DAL": 0}, false},
	} {
		t.Run(tt.name, func(t *testing.T) {
			if got := allGamesComplete(tt.statuses); got != tt.want {
				t.Fatalf("allGamesComplete() = %v, want %v", got, tt.want)
			}
		})
	}
}
