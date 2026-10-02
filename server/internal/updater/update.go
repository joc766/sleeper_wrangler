package updater

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"maps"
	"os"
	"os/exec"
	"path/filepath"
	"time"

	"github.com/joc766/sleeper/losers/server/internal/hub"
	"github.com/joc766/sleeper/losers/server/internal/sqlc"
)

func getPythonDir() (string, error) {
	pyDir, ok := os.LookupEnv("PY_DIR")
	if !ok {
		return "", fmt.Errorf("set PY_DIR to the python project directory")
	}

	if info, err := os.Stat(pyDir); err != nil {
		return "", fmt.Errorf("PY_DIR does not exist; set PY_DIR to the python project directory")
	} else if !info.IsDir() {
		return "", fmt.Errorf("PY_DIR must be a directory")
	}
	return pyDir, nil
}

func runPythonLoserSimulation(ctx context.Context) (hub.Update, error) {
	pyDir, err := getPythonDir()
	if err != nil {
		return hub.Update{}, err
	}
	cmd := exec.CommandContext(
		ctx,
		filepath.Join(pyDir, ".venv", "/bin", "/python"),
		"-m", "sleeper_wrangler.losers",
	)
	cmd.Dir = pyDir

	var outBuffer, stderr bytes.Buffer
	cmd.Stdout = &outBuffer
	cmd.Stderr = &stderr

	if err := cmd.Run(); err != nil {
		return hub.Update{}, fmt.Errorf("Python simulation failed: %w; stderr: %s", err, stderr.String())
	}

	var update hub.Update
	if err := json.Unmarshal(outBuffer.Bytes(), &update); err != nil {
		return hub.Update{}, fmt.Errorf("invalid simulation JSON: %w; stdout: %q", err, outBuffer.String())
	}
	return update, nil
}

func GetLatestGameStatus(ctx context.Context, queries *sqlc.Queries) (map[string]float64, error) {
	row, err := queries.GetLatestProjection(ctx)
	if err != nil {
		return nil, err
	}

	var data []byte
	switch value := row.Gamestatus.(type) {
	case string:
		data = []byte(value)
	case []byte:
		data = value
	case nil:
		return nil, nil
	default:
		return nil, fmt.Errorf("unexpected GameStatus type %T", value)
	}

	var status map[string]float64
	if err := json.Unmarshal(data, &status); err != nil {
		return nil, fmt.Errorf("unexpected game status json: %w", err)
	}
	return status, nil
}

func CheckNewGameStatus(ctx context.Context, queries *sqlc.Queries) bool {
	latestStatus, err := GetLatestGameStatus(ctx, queries)
	if err != nil && !errors.Is(err, sql.ErrNoRows) {
		log.Println(err)
		return false
	} else {
		currentStatus, err := getGameStatuses(ctx)
		if err != nil {
			log.Println(err)
			return false
		}
		return !maps.Equal(latestStatus, currentStatus)
	}
}

// TODO: also check if matchupRoster.starters_points JSONs have changed at all
// (checks boths player IDs and points that way)
func RunUpdater(ctx context.Context, queries *sqlc.Queries, updates chan hub.Update) {
	for {
		if ctx.Err() != nil {
			return
		}
		if CheckNewGameStatus(ctx, queries) {
			if update, err := runPythonLoserSimulation(ctx); err != nil {
				log.Printf("Error during simulation: %v", err)
			} else {
				select {
				case updates <- update:
				case <-ctx.Done():
					return
				}
			}
		}

		select {
		case <-time.After(time.Second * 60):
		case <-ctx.Done():
			return
		}
	}
}
