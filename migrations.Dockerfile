FROM golang:1.27 AS go-builder

RUN CGO_ENABLED=0 \
    go install github.com/pressly/goose/v3/cmd/goose@latest

FROM alpine:latest

COPY --from=go-builder /go/bin/goose /usr/local/bin/goose

WORKDIR /migrations

COPY sql/schema/ .

CMD ["goose", "-dir", "/migrations", "sqlite3", "/data/db.sqlite3", "up"]
