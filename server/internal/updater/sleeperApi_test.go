package updater

import (
	"context"
	"testing"
)

func Test_getNFLState(t *testing.T) {
	result, err := getNFLState(context.Background())
	if err != nil {
		t.Fatalf("Error: %v", err)
	}
	t.Logf("%+v", result)
}
