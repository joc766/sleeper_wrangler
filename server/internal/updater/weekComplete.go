package updater

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"

	"github.com/joc766/sleeper/losers/server/internal/sqlc"
)

// IsWeekComplete uses the statuses saved with the latest simulation.
func IsWeekComplete(ctx context.Context, queries *sqlc.Queries, season string, week int) (bool, error) {
	row, err := queries.GetLatestProjection(ctx)
	if errors.Is(err, sql.ErrNoRows) {
		return false, nil
	}
	if err != nil {
		return false, err
	}
	if !row.Season.Valid || !row.Week.Valid || row.Season.String != season || row.Week.Int64 != int64(week) {
		return false, nil
	}
	var data []byte
	switch value := row.Gamestatus.(type) {
	case nil:
		return false, nil
	case string:
		data = []byte(value)
	case []byte:
		data = value
	default:
		return false, fmt.Errorf("unexpected GameStatus type %T", value)
	}
	var statuses map[string]float64
	if err := json.Unmarshal(data, &statuses); err != nil {
		return false, fmt.Errorf("decode stored game statuses: %w", err)
	}
	return allGamesComplete(statuses), nil
}

func allGamesComplete(statuses map[string]float64) bool {
	if len(statuses) == 0 {
		return false
	}
	for _, completion := range statuses {
		if completion != 1.0 {
			return false
		}
	}
	return true
}
