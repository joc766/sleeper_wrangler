package main

import (
	"context"
	"database/sql"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/joc766/sleeper/losers/server/internal/hub"
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
			db, err := sql.Open("sqlite", ":memory:")
			if err != nil {
				t.Fatal(err)
			}
			defer db.Close()
			if _, err := db.Exec("CREATE TABLE LoserProjections (LoserProjectionID INTEGER PRIMARY KEY, ProjectionData TEXT)"); err != nil {
				t.Fatal(err)
			}
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
				handleEvents(ctx, db, h)(w, r)
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
