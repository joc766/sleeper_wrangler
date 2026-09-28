package updater

import "testing"

func Test_getGameStatuses(t *testing.T) {
	result, _ := getGameStatuses()
	t.Log(result)
}
