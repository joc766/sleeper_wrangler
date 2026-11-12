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

func ParseWeekStatus(row sqlc.GetLatestProjectionRow) (map[string]float64, error) {
	var data []byte
	switch value := row.Gamestatus.(type) {
	case nil:
		return nil, fmt.Errorf("empty game status returned from LoserProjections")
	case string:
		data = []byte(value)
	case []byte:
		data = value
	default:
		return nil, fmt.Errorf("unexpected GameStatus type %T", value)
	}
	var statuses map[string]float64
	if err := json.Unmarshal(data, &statuses); err != nil {
		return nil, fmt.Errorf("decode stored game statuses: %w", err)
	}

	return statuses, nil

}

// IsWeekComplete uses the statuses saved with the latest simulation.
func GetWeekStatus(ctx context.Context, queries *sqlc.Queries) (WeekStatus, error) {
	row, err := queries.GetLatestProjection(ctx)
	if errors.Is(err, sql.ErrNoRows) {
		return WeekStatus{}, fmt.Errorf("LoserProjections returned no rows")
	}
	if err != nil {
		return WeekStatus{}, err
	}
	if !row.Season.Valid || !row.Week.Valid {
		return WeekStatus{}, fmt.Errorf("invalid season or week returned from LoserProjections")
	}
	statuses, err := ParseWeekStatus(row)
	if err != nil {
		return WeekStatus{}, err
	}

	return WeekStatus{
		Season:     row.Season.String,
		Week:       row.Week.Int64,
		IsComplete: AllGamesComplete(statuses),
	}, nil
}

func AllGamesComplete(statuses map[string]float64) bool {
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
