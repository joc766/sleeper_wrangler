package updater

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
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
	// TODO: have the loser simulation store some kind of matchup object to detect changes
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

func RunUpdater(ctx context.Context, database *sql.DB, queries *sqlc.Queries, updates chan hub.Update) {
	nextProjectionCheck := time.Time{}
	for {
		if ctx.Err() != nil {
			return
		}
		nflState, err := getNFLState(ctx)
		if err != nil {
			log.Printf("Error checking NFL State: %v", err)
			continue
		}
		gameStatusChanged, err := CheckNewGameStatus(ctx, queries, nflState.SeasonStartDate, nflState.Week)
		if err != nil {
			log.Printf("Error checking game status: %v", err)
		}

		matchupsChanged, err := CheckNewMatchups(ctx, queries, nflState.Season, nflState.Week)
		if err != nil {
			log.Printf("Error checking new matchups: %v", err)
		}
		// don't want to abuse the projections endpoint since it's undocumented, so only check every 30 min
		projectionsChanged := false
		if !time.Now().Before(nextProjectionCheck) {
			projectionsChanged, err = CheckNewProjections(ctx, database, queries, nflState.Season, nflState.Week)
			if err != nil {
				log.Printf("Error checking matchups: %v", err)
			} else {
				nextProjectionCheck = time.Now().Add(time.Minute * 30)
			}
		}
		if gameStatusChanged || matchupsChanged || projectionsChanged {
			log.Printf("gameStatusChanged: %v, matchupsChanged: %v, projectionsChanged: %v", gameStatusChanged, matchupsChanged, projectionsChanged)
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
		case <-time.After(time.Minute):
		case <-ctx.Done():
			return
		}
	}
}
