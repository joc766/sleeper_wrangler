package main

import (
	"context"
	"database/sql"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/joc766/sleeper/losers/server/internal/hub"
	"github.com/joc766/sleeper/losers/server/internal/sqlc"
)

type flushRecorder struct {
	*httptest.ResponseRecorder
	flushed chan struct{}
}

func (w *flushRecorder) Flush() {
	w.ResponseRecorder.Flush()
	select {
	case w.flushed <- struct{}{}:
	default:
	}
}

func TestEventsCancellation(t *testing.T) {
	for _, shutdown := range []bool{false, true} {
		name := "client disconnect"
		if shutdown {
			name = "application shutdown"
		}
		t.Run(name, func(t *testing.T) {
			database, err := sql.Open("sqlite", ":memory:")
			if err != nil {
				t.Fatal(err)
			}
			defer database.Close()
			if _, err := database.Exec("CREATE TABLE LoserProjections (LoserProjectionID INTEGER PRIMARY KEY, ProjectionData TEXT, CreatedAt TEXT, Gamestatus TEXT)"); err != nil {
				t.Fatal(err)
			}
			queries := sqlc.New(database)
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			h := hub.NewHub()
			go h.Run(ctx)
			requestCtx, disconnect := context.WithCancel(context.Background())
			defer disconnect()
			r := httptest.NewRequest("GET", "/events", nil).WithContext(requestCtx)
			w := &flushRecorder{httptest.NewRecorder(), make(chan struct{}, 1)}
			done := make(chan struct{})
			go func() {
				handleEvents(ctx, queries, h)(w, r)
				close(done)
			}()
			select {
			case <-w.flushed:
			case <-time.After(2 * time.Second):
				t.Fatal("SSE connection did not open with an empty projections table")
			}
			if shutdown {
				cancel()
			} else {
				disconnect()
			}
			select {
			case <-done:
			case <-time.After(2 * time.Second):
				t.Fatal("SSE handler did not exit after cancellation")
			}
		})
	}
}
