package updater

import (
	"database/sql"
	"io"
	"net/http"
	"strings"
	"testing"

	"github.com/joc766/sleeper/losers/server/internal/sqlc"
	_ "modernc.org/sqlite"
)

type injuryTransport func(*http.Request) (*http.Response, error)

func (f injuryTransport) RoundTrip(r *http.Request) (*http.Response, error) {
	return f(r)
}

func TestInjuryOnlyProjectionChanges(t *testing.T) {
	for _, tc := range []struct {
		name    string
		stored  any
		api     string
		changed bool
		want    sql.NullString
	}{
		{"new injury", "Questionable", "Out", true, sql.NullString{String: "Out", Valid: true}},
		{"recovered", "Out", "", true, sql.NullString{}},
		{"explicit healthy", "Out", "Healthy", true, sql.NullString{}},
		{"unchanged", "Out", "Out", false, sql.NullString{String: "Out", Valid: true}},
		{"healthy null", nil, "", false, sql.NullString{}},
		{"normalized", "Out", " out ", false, sql.NullString{String: "Out", Valid: true}},
	} {
		t.Run(tc.name, func(t *testing.T) {
			db, err := sql.Open("sqlite", ":memory:")
			if err != nil {
				t.Fatal(err)
			}
			defer db.Close()
			_, err = db.Exec(`
				CREATE TABLE League (LeagueID TEXT, Season TEXT, ScoringSettings TEXT);
				INSERT INTO League VALUES ('league', '2026', '{"pass_yd":0.04}');
				CREATE TABLE MatchupRoster (MatchupRosterID INTEGER, LeagueID TEXT, Week INTEGER);
				INSERT INTO MatchupRoster VALUES (1,'league',10);
				CREATE TABLE MatchupRosterPlayer (MatchupRosterID INTEGER, PlayerID TEXT, Starter INTEGER);
				INSERT INTO MatchupRosterPlayer VALUES (1,'player',1);
				CREATE TABLE Projections (
					PlayerID TEXT, Season TEXT, Week INTEGER, Date DATE, InjuryStatus TEXT,
					PointsHalfPPR REAL, PointsNoTDs REAL, TDStats TEXT,
					UNIQUE(Season, Week, PlayerID));
			`)
			if err != nil {
				t.Fatal(err)
			}
			_, err = db.Exec(`INSERT INTO Projections VALUES ('player','2026',10,NULL,?,4,4,'{}')`, tc.stored)
			if err != nil {
				t.Fatal(err)
			}
			original := http.DefaultTransport
			http.DefaultTransport = injuryTransport(func(r *http.Request) (*http.Response, error) {
				if r.URL.Host != "api.sleeper.app" {
					t.Fatalf("unexpected request: %s", r.URL)
				}
				return &http.Response{
					StatusCode: 200,
					Header:     make(http.Header),
					Body:       io.NopCloser(strings.NewReader(`[{"player_id":"player","stats":{"pass_yd":100},"player":{"injury_status":"` + tc.api + `"}}]`)),
				}, nil
			})
			defer func() { http.DefaultTransport = original }()
			q := sqlc.New(db)
			changed, err := CheckNewProjections(t.Context(), db, q, "2026", 10)
			if err != nil || changed != tc.changed {
				t.Fatalf("changed=%v err=%v", changed, err)
			}
			var got sql.NullString
			if err := db.QueryRow(`SELECT InjuryStatus FROM Projections`).Scan(&got); err != nil {
				t.Fatal(err)
			}
			if got != tc.want {
				t.Fatalf("status=%v, want %v", got, tc.want)
			}
			changed, err = CheckNewProjections(t.Context(), db, q, "2026", 10)
			if err != nil || changed {
				t.Fatalf("repeat check: changed=%v err=%v", changed, err)
			}
		})
	}
}
