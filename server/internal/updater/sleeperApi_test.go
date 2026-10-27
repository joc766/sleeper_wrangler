package updater

import (
	"context"
	"testing"
)

func Test_getNFLState(t *testing.T) {
	result, err := GetNFLState(context.Background())
	if err != nil {
		t.Fatalf("Error: %v", err)
	}
	t.Logf("%+v", result)
}

func Test_getMatchupStarters(t *testing.T) {
	tests := []struct {
		name string // description of this test case
		// Named input parameters for target function.
		leagueid string
		week     int
		want     starterMap
		wantErr  bool
	}{
		{
			name:     "test 1",
			leagueid: "1384538107809902592",
			week:     5,
			want:     nil,
			wantErr:  false,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, gotErr := getMatchupStarters(t.Context(), tt.leagueid, tt.week)
			if gotErr != nil {
				if !tt.wantErr {
					t.Errorf("getMatchupStarters() failed: %v", gotErr)
				}
				return
			}
			if tt.wantErr {
				t.Fatal("getMatchupStarters() succeeded unexpectedly")
			}
			// TODO: update the condition below to compare got with tt.want.
			t.Logf("%+v", got)
			if false {
				t.Errorf("getMatchupStarters() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestGetProjections(t *testing.T) {
	tests := []struct {
		name string // description of this test case
		// Named input parameters for target function.
		season  string
		week    int
		want    []PlayerProjection
		wantErr bool
	}{
		{
			name:    "test 1",
			season:  "2026",
			week:    1,
			want:    nil,
			wantErr: false,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			_, gotErr := GetProjections(tt.season, tt.week)
			if gotErr != nil {
				if !tt.wantErr {
					t.Errorf("GetProjections() failed: %v", gotErr)
				}
				return
			}
			if tt.wantErr {
				t.Fatal("GetProjections() succeeded unexpectedly")
			}
			// TODO: update the condition below to compare got with tt.want.
			// if true {
			// 	t.Errorf("GetProjections() = %v, want %v", got, tt.want)
			// }
		})
	}
}
