package updater

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"

	"github.com/joc766/sleeper/losers/server/internal/sqlc"
)

type WeekStatus struct {
	Season     string
	Week       int64
	IsComplete bool
}

// IsWeekComplete uses the statuses saved with the latest simulation.
func GetWeekStatus(ctx context.Context, queries *sqlc.Queries) (WeekStatus, error) {
	row, err := queries.GetLatestProjection(ctx)
	if errors.Is(err, sql.ErrNoRows) {
		return WeekStatus{}, fmt.Errorf("LoserProjections returned no rows.")
	}
	if err != nil {
		return WeekStatus{}, err
	}
	if !row.Season.Valid || !row.Week.Valid {
		return WeekStatus{}, fmt.Errorf("invalid season or week returned from LoserProjections.")
	}
	var data []byte
	switch value := row.Gamestatus.(type) {
	case nil:
		return WeekStatus{}, fmt.Errorf("empty game status returned from LoserProjections.")
	case string:
		data = []byte(value)
	case []byte:
		data = value
	default:
		return WeekStatus{}, fmt.Errorf("unexpected GameStatus type %T", value)
	}
	var statuses map[string]float64
	if err := json.Unmarshal(data, &statuses); err != nil {
		return WeekStatus{}, fmt.Errorf("decode stored game statuses: %w", err)
	}
	return WeekStatus{
		Season:     row.Season.String,
		Week:       row.Week.Int64,
		IsComplete: allGamesComplete(statuses),
	}, nil
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
