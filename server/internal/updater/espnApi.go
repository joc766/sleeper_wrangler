package updater

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

type Competitor struct {
	Abbr string `json:"abbreviation"`
}

type Event struct {
	ID              string       `json:"id"`
	Competitors     []Competitor `json:"competitors"`
	PercentComplete float64      `json:"percentComplete"`
}

type GameStatusResponse struct {
	Stats  []any   `json:"statistics"`
	Events []Event `json:"events"`
}

func getGameStatuses(ctx context.Context) (map[string]float64, error) {
	/*
	 * Returns map of team abbreviations as keys
	 * and float of percent complete as values
	 */
	completionByTeam := make(map[string]float64)
	abbrCorrections := make(map[string]string)
	abbrCorrections["WSH"] = "WAS"
	URL := "https://site.web.api.espn.com/apis/fantasy/v2/games/ffl/games"
	req, err := http.NewRequestWithContext(ctx, "GET", URL, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Accept", "application/json")
	client := &http.Client{
		Timeout: 5 * time.Second,
	}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("ESPN game statuses: unexpected HTTP status %s", resp.Status)
	}
	var data GameStatusResponse
	if err := json.NewDecoder(resp.Body).Decode(&data); err != nil {
		return nil, err
	}
	for _, e := range data.Events {
		for _, c := range e.Competitors {
			abbr := c.Abbr
			if correction, ok := abbrCorrections[abbr]; ok {
				abbr = correction
			}
			completionByTeam[abbr] = float64(e.PercentComplete) / 100.0
		}
	}

	return completionByTeam, nil
}
