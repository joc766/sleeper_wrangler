package updater

import (
	"context"
	"encoding/json"
	"net/http"
	"strings"
	"time"
)

type NFLState struct {
	Week            int    `json:"week"`
	Season          string `json:"season"`
	SeasonType      string `json:"season_type"`
	SeasonHasScores bool   `json:"season_has_scores"`
	SeasonStartDate Date   `json:"season_start_date"`
}

type Date time.Time

func (d *Date) UnmarshalJSON(b []byte) error {
	s := strings.Trim(string(b), `"`)

	t, err := time.Parse("2006-01-02", s)
	if err != nil {
		return err
	}

	*d = Date(t)
	return nil
}

func getNFLState(ctx context.Context) (NFLState, error) {
	URL := "https://api.sleeper.app/v1/state/nfl"
	client := http.Client{
		Timeout: time.Second * 5,
	}
	req, err := http.NewRequestWithContext(ctx, "GET", URL, nil)
	if err != nil {
		return NFLState{}, err
	}
	resp, err := client.Do(req)
	if err != nil {
		return NFLState{}, err
	}
	defer resp.Body.Close()
	var state NFLState
	if err = json.NewDecoder(resp.Body).Decode(&state); err != nil {
		return NFLState{}, err
	}
	return state, nil
}
