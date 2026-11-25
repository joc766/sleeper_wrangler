package main

import (
	"fmt"
	"os"
	"time"
)

func lookupProjectionPollInterval() (time.Duration, error) {
	value := os.Getenv("PROJECTION_POLL_INTERVAL")
	if value == "" {
		return 30 * time.Minute, nil
	}
	interval, err := time.ParseDuration(value)
	if err != nil || interval < time.Minute {
		return 0, fmt.Errorf("invalid PROJECTION_POLL_INTERVAL %q: use a duration of at least 1m", value)
	}
	return interval, nil
}
