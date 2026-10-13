package updater

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"maps"
	"math"
	"slices"
	"sort"
	"time"

	"github.com/joc766/sleeper/losers/server/internal/sqlc"
)

type RosterInfo struct {
	Starters []string
	Points   float64
}

type starterMap = map[int64]RosterInfo

func getLatestGameStatus(ctx context.Context, queries *sqlc.Queries) (map[string]float64, error) {
	row, err := queries.GetLatestProjection(ctx)
	if err != nil {
		return nil, err
	}

	var data []byte
	switch value := row.Gamestatus.(type) {
	case string:
		data = []byte(value)
	case []byte:
		data = value
	case nil:
		return nil, nil
	default:
		return nil, fmt.Errorf("unexpected GameStatus type %T", value)
	}

	var status map[string]float64
	if err := json.Unmarshal(data, &status); err != nil {
		return nil, fmt.Errorf("unexpected game status json: %w", err)
	}
	return status, nil
}

func CheckNewGameStatus(ctx context.Context, queries *sqlc.Queries, seasonStartDate Date, week int) (bool, error) {
	/* Returns true if game status has changed since last simulation, false otherwise. */
	latestStatus, err := getLatestGameStatus(ctx, queries)
	if err != nil && !errors.Is(err, sql.ErrNoRows) {
		return false, err
	} else {
		if err != nil {
			return false, err
		}
		startWeekOffsetDays := 7 * (week - 1)
		endWeekOffsetDays := (7 * week) - 1
		tStart := time.Time(seasonStartDate).AddDate(0, 0, startWeekOffsetDays)
		tEnd := time.Time(seasonStartDate).AddDate(0, 0, endWeekOffsetDays)
		currentStatus, err := getGameStatuses(ctx, tStart, tEnd)
		if err != nil {
			return false, err
		}
		return !maps.Equal(latestStatus, currentStatus), nil
	}
}

// One question: should we move the matchup updating logic out of losers/__main__.py and put it here?
// Might then need to put the logic of updating the database with the new simulation into Go.
// Does that complicate manual updates? Might make it unnecessary anyway...
// Plus, makes it more possible to add an API endpoint to run this manual update

func getDBStarters(ctx context.Context, queries *sqlc.Queries, leagueID string, week int) (starterMap, error) {
	dbStarterRows, err := queries.GetStarters(ctx, sqlc.GetStartersParams{
		Leagueid: leagueID,
		Week:     int64(week),
	})
	if err != nil {
		return nil, err
	}
	dbStarters := make(starterMap, len(dbStarterRows))
	for _, row := range dbStarterRows {
		var data []string
		err := json.Unmarshal([]byte(row.Starters), &data)
		if err != nil {
			return nil, fmt.Errorf("unexpected error unmarshaling sql starters: %v", row.Starters)
		}
		dbStarters[row.Rostercode] = RosterInfo{
			Starters: data,
			Points:   row.Points.Float64,
		}
	}
	return dbStarters, nil
}

func getAPIStarters(ctx context.Context, leagueID string, week int) (starterMap, error) {
	apiStartersSlice, err := getMatchupStarters(ctx, leagueID, week)
	if err != nil {
		return nil, err
	}
	apiStarters := make(starterMap, len(apiStartersSlice))
	for _, rosterData := range apiStartersSlice {
		apiStarters[rosterData.RosterCode] = RosterInfo{
			Starters: rosterData.Starters,
			Points:   rosterData.Points,
		}
	}
	return apiStarters, nil
}

func equalRosterInfo(a, b RosterInfo) bool {
	return slices.Equal(a.Starters, b.Starters) && a.Points == b.Points
}

// TODO: update matchups here if we find that it's true?
func CheckNewMatchups(ctx context.Context, queries *sqlc.Queries, season string, week int) (bool, error) {
	/* Returns true if matchup starter IDs or scores have changed since last simulation, false otherwise */
	leagueID, err := queries.GetLeagueIDBySeason(ctx, season)
	if err != nil {
		return false, err
	}

	dbStarters, err := getDBStarters(ctx, queries, leagueID, week)
	if err != nil {
		return false, err
	}
	apiStarters, err := getAPIStarters(ctx, leagueID, week)
	if err != nil {
		return false, err
	}

	if !maps.EqualFunc(apiStarters, dbStarters, equalRosterInfo) {
		return true, nil
	}

	return false, nil
}

func cleanProjections(apiData []PlayerProjection, leagueSettings map[string]float64, playerIDs map[string]struct{}) map[string]float64 {
	/* Calculate projections according to league settings for only the players that we care about */
	projections := make(map[string]float64, len(playerIDs))
	for _, pp := range apiData {
		if _, ok := playerIDs[pp.PlayerID]; ok {
			projPoints := 0.0
			// order statKeys to make projPoints determininstic given same inputs
			statKeys := make([]string, 0, len(pp.Stats))
			for statKey := range pp.Stats {
				statKeys = append(statKeys, statKey)
			}
			sort.Strings(statKeys)
			for _, statKey := range statKeys {
				projAmount := pp.Stats[statKey]
				if statValue, ok := leagueSettings[statKey]; ok {
					projPoints += statValue * projAmount
				}
			}
			projections[pp.PlayerID] = math.Trunc(projPoints*100) / 100
		}
	}

	return projections
}

func getLeagueScoreSettings(ctx context.Context, queries *sqlc.Queries, leagueID string) (map[string]float64, error) {
	leagueSettingsString, err := queries.GetLeagueScoringSettings(ctx, leagueID)
	if err != nil {
		return nil, err
	}
	if !leagueSettingsString.Valid {
		return nil, fmt.Errorf("missing league settings in db for leagueID: %s", leagueID)
	}
	var leagueSettings map[string]float64
	if err := json.Unmarshal([]byte(leagueSettingsString.String), &leagueSettings); err != nil {
		return nil, err
	}
	return leagueSettings, nil

}

func CheckNewProjections(ctx context.Context, database *sql.DB, queries *sqlc.Queries, season string, week int) (bool, error) {
	apiProjectionData, err := GetProjections(season, week)
	if err != nil {
		return false, err
	}

	leagueID, err := queries.GetLeagueIDBySeason(ctx, season)
	if err != nil {
		return false, err
	}

	leagueSettings, err := getLeagueScoreSettings(ctx, queries, leagueID)
	if err != nil {
		return false, err
	}

	includedPlayers := make(map[string]struct{})
	playersSlice, err := queries.GetMatchupPlayers(ctx, sqlc.GetMatchupPlayersParams{
		Leagueid: leagueID,
		Week:     int64(week),
	})
	for _, p := range playersSlice {
		includedPlayers[p] = struct{}{}
	}

	apiProjections := cleanProjections(apiProjectionData, leagueSettings, includedPlayers)

	dbProjectionRows, err := queries.GetProjections(ctx, sqlc.GetProjectionsParams{
		Season:    season,
		Week:      int64(week),
		PlayerIds: playersSlice,
	})
	if err != nil {
		return false, err
	}
	dbProjections := make(map[string]float64, len(playersSlice))
	for _, p := range dbProjectionRows {
		if !p.Pointshalfppr.Valid {
			dbProjections[p.Playerid] = 0.0
		} else {
			dbProjections[p.Playerid] = p.Pointshalfppr.Float64
		}
	}

	projectionsChanged := !maps.Equal(apiProjections, dbProjections)
	if projectionsChanged {
		if err := updateProjections(ctx, database, queries, apiProjectionData, leagueSettings, season, week); err != nil {
			return false, fmt.Errorf("update projections: %w", err)
		}
	}
	return projectionsChanged, nil
}

func updateProjections(ctx context.Context, database *sql.DB, queries *sqlc.Queries, apiData []PlayerProjection, leagueSettings map[string]float64, season string, week int) error {
	allPlayers := make(map[string]struct{}, len(apiData))
	for _, projection := range apiData {
		allPlayers[projection.PlayerID] = struct{}{}
	}
	projections := cleanProjections(apiData, leagueSettings, allPlayers)

	tx, err := database.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	txQueries := queries.WithTx(tx)

	for _, projection := range apiData {
		var projectionDate sql.NullTime
		if projection.Date != "" {
			parsedDate, err := time.Parse(time.RFC3339, projection.Date)
			if err != nil {
				parsedDate, err = time.Parse("2006-01-02", projection.Date)
				if err != nil {
					return fmt.Errorf("parse projection date %q: %w", projection.Date, err)
				}
			}
			projectionDate = sql.NullTime{Time: parsedDate, Valid: true}
		}

		injuryStatus := interface{}(projection.Player.InjuryStatus)
		if projection.Player.InjuryStatus == "" {
			injuryStatus = nil
		}
		if err := txQueries.UpsertProjection(ctx, sqlc.UpsertProjectionParams{
			Date:          projectionDate,
			Season:        season,
			Week:          int64(week),
			Playerid:      projection.PlayerID,
			Injurystatus:  injuryStatus,
			Pointshalfppr: sql.NullFloat64{Float64: projections[projection.PlayerID], Valid: true},
		}); err != nil {
			return fmt.Errorf("upsert projection for player %s: %w", projection.PlayerID, err)
		}
	}
	return tx.Commit()
}
