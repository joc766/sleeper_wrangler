package updater

import (
	"reflect"
	"testing"
)

func TestCleanProjectionsIncludesNoTDAndTDStats(t *testing.T) {
	got, err := cleanProjections([]PlayerProjection{
		{
			PlayerID: "player-1",
			Stats: map[string]float64{
				"pass_yd": 200,
				"pass_td": 2,
				"rec_td":  1,
			},
		},
		{PlayerID: "player-2", Stats: map[string]float64{}},
	}, map[string]float64{
		"pass_yd": 0.04,
		"pass_td": 4,
		"rec_td":  6,
	}, map[string]struct{}{"player-1": {}, "player-2": {}})
	if err != nil {
		t.Fatalf("cleanProjections() error = %v", err)
	}

	want := map[string]projectionValues{
		"player-1": {PointsHalfPPR: 22, PointsNoTDs: 8, TDStats: `{"pass_td":2,"rec_td":1}`},
		"player-2": {PointsHalfPPR: 0, PointsNoTDs: 0, TDStats: `{}`},
	}
	if !reflect.DeepEqual(got, want) {
		t.Errorf("cleanProjections() = %#v, want %#v", got, want)
	}
}

func TestCanonicalTDStatsIgnoresJSONKeyOrder(t *testing.T) {
	got, err := canonicalTDStats(`{"rec_td":1,"pass_td":2}`)
	if err != nil {
		t.Fatalf("canonicalTDStats() error = %v", err)
	}
	if want := `{"pass_td":2,"rec_td":1}`; got != want {
		t.Errorf("canonicalTDStats() = %s, want %s", got, want)
	}
}
