package updater

import (
	"context"
	"testing"
	"time"
)

func Test_getGameStatuses(t *testing.T) {
	tStart, err := time.Parse("2006-01-02", "2026-10-05")
	if err != nil {
		t.Fatalf("Error: %v", err)
	}
	tEnd, err := time.Parse("2006-01-02", "2026-10-11")
	if err != nil {
		t.Fatalf("Error: %v", err)
	}
	result, err := getGameStatuses(context.Background(), tStart, tEnd)
	if err != nil {
		t.Fatalf("Error: %v", err)
	}
	t.Log(result)
}
