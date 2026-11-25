package hub

import (
	"encoding/json"
	"testing"
)

func TestInjuryMetadataRoundTrip(t *testing.T) {
	var update Update
	if err := json.Unmarshal([]byte(`{"injured_starters":{"manager":{"player":"Out"}}}`), &update); err != nil {
		t.Fatal(err)
	}
	data, err := json.Marshal(update)
	if err != nil {
		t.Fatal(err)
	}
	var got Update
	if err := json.Unmarshal(data, &got); err != nil {
		t.Fatal(err)
	}
	if got.InjuredStarters["manager"]["player"] != "Out" {
		t.Fatalf("injury lost in event round trip: %s", data)
	}
}
