package updater

import (
	"context"
	"testing"
)

func Test_getGameStatuses(t *testing.T) {
	result, _ := getGameStatuses(context.Background())
	t.Log(result)
}
