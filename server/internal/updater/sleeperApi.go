package updater

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"
)

type NFLState struct {
	Week            int    `json:"display_week"`
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

func GetNFLState(ctx context.Context) (NFLState, error) {
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

type MatchupRosterResponseRow struct {
	Points         float64            `json:"points"`
	Players        []string           `json:"players"`
	RosterCode     int64              `json:"roster_id"`
	Starters       []string           `json:"starters"`
	StartersPoints []float64          `json:"starters_points"`
	PlayersPoints  map[string]float64 `json:"players_points"`
}

func getMatchupStarters(ctx context.Context, leagueid string, week int) ([]MatchupRosterResponseRow, error) {
	URL := fmt.Sprintf("https://api.sleeper.app/v1/league/%v/matchups/%v", leagueid, week)
	client := http.Client{
		Timeout: time.Second * 5,
	}
	req, err := http.NewRequestWithContext(ctx, "GET", URL, nil)
	if err != nil {
		return nil, err
	}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var data []MatchupRosterResponseRow
	if err = json.NewDecoder(resp.Body).Decode(&data); err != nil {
		return nil, err
	}
	return data, err
}

type PlayerProjection struct {
	Date     string             `json:"date"`
	Stats    map[string]float64 `json:"stats"`
	Season   string             `json:"season"`
	Week     int                `json:"week"`
	PlayerID string             `json:"player_id"`
	Player   struct {
		InjuryStatus string `json:"injury_status"`
	} `json:"player"`
}

func GetProjections(season string, week int) ([]PlayerProjection, error) {
	URL := fmt.Sprintf("https://api.sleeper.app/projections/nfl/%s/%d?position[]=QB&position[]=RB&position[]=WR&position[]=TE&position[]=K&position[]=DEF&season_type=regular", season, week)
	client := http.Client{
		Timeout: time.Second * 5,
	}
	req, err := http.NewRequest("GET", URL, nil)
	if err != nil {
		return nil, err
	}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var data []PlayerProjection
	if err = json.NewDecoder(resp.Body).Decode(&data); err != nil {
		return nil, err
	}
	return data, nil
}
