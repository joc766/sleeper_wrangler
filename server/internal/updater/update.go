package updater

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os/exec"
	"path/filepath"
	"time"

	"github.com/joc766/sleeper/losers/server/internal/hub"
)

func runPythonLoserSimulation(ctx context.Context) (hub.Update, error) {
	projectDir := "/Users/jack/workspace/github.com/joc766/sleeper_wrangler/py"
	cmd := exec.CommandContext(
		ctx,
		filepath.Join(projectDir, ".venv", "/bin", "/python"),
		"-m", "sleeper_wrangler.losers",
	)
	cmd.Dir = projectDir

	var outBuffer, stderr bytes.Buffer
	cmd.Stdout = &outBuffer
	cmd.Stderr = &stderr

	if err := cmd.Run(); err != nil {
		return nil, fmt.Errorf("Python simulation failed: %w; stderr: %s", err, stderr.String())
	}

	var update hub.Update
	if err := json.Unmarshal(outBuffer.Bytes(), &update); err != nil {
		return nil, fmt.Errorf("invalid simulation JSON: %w; stdout: %q", err, outBuffer.String())
	}
	return update, nil
}

func RunUpdater(ctx context.Context, updates chan hub.Update) {
	for {
		if ctx.Err() != nil {
			return
		}
		update, err := runPythonLoserSimulation(ctx)
		if ctx.Err() != nil {
			return
		}
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
