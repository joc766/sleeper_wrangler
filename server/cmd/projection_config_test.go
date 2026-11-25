package main

import (
	"testing"
	"time"
)

func TestProjectionPollInterval(t *testing.T) {
	for _, tc := range []struct {
		value   string
		want    time.Duration
		invalid bool
	}{
		{"", 30 * time.Minute, false},
		{"5m", 5 * time.Minute, false},
		{"1m", time.Minute, false},
		{"1h", time.Hour, false},
		{"0", 0, true},
		{"-5m", 0, true},
		{"30s", 0, true},
		{"five", 0, true},
	} {
		t.Run(tc.value, func(t *testing.T) {
			t.Setenv("PROJECTION_POLL_INTERVAL", tc.value)
			got, err := lookupProjectionPollInterval()
			if (err != nil) != tc.invalid || got != tc.want {
				t.Fatalf("got %v, %v; want %v, invalid=%v", got, err, tc.want, tc.invalid)
			}
		})
	}
}
