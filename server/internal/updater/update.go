package updater

import (
	"bytes"
	"context"
	"encoding/json"
	"log"
	"os/exec"
	"time"

	"github.com/joc766/sleeper/losers/server/internal/hub"
)

func runPythonLoserSimulation(ctx context.Context) (hub.Update, error) {
	cmd := exec.CommandContext(ctx, "uv", "run", "python", "-m", "losers")

	var outBuffer bytes.Buffer
	cmd.Stdout = &outBuffer

	cmd.Run()

	var update hub.Update
	if err := json.Unmarshal(outBuffer.Bytes(), &update); err != nil {
		return nil, err
	}
	return update, nil
}

func RunUpdater(ctx context.Context, updates chan hub.Update) {
	for {
		update, err := runPythonLoserSimulation(ctx)
		if err != nil {
			log.Printf("Error during simulation: %v", err)
		} else {
			select {
			case updates <- update:
			case <-ctx.Done():
				return
			}
		}

		select {
		case <-time.After(time.Second * 60):
		case <-ctx.Done():
			return
		}
	}
}
