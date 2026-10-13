#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/home/jackoconnor/Projects/gh/sleeper_wrangler"
PY_DIR="$APP_DIR/py"
SRV_DIR="$APP_DIR/server"
export GOOSE_DRIVER="sqlite3"
export GOOSE_DBSTRING="/var/lib/sleeper-wrangler/db.sqlite3"
export GOOSE_MIGRATION_DIR="$APP_DIR/sql/schema"

SERVICE="sleeper-server.service"

echo "Updating source..."
cd "$APP_DIR"
git pull --ff-only

echo "Installing/updating dependencies..."
cd "$PY_DIR"
uv sync --frozen

echo "Building..."
cd "$SRV_DIR"
go build -o /tmp/sleeper-server ./cmd

echo "Installing binary..."
sudo install -m 755 /tmp/sleeper-server /usr/local/bin/sleeper-server

echo "Applying database migrations..."
goose up

echo "Restarting service"
sudo systemctl restart "$SERVICE"

echo "Checking service..."
sudo systemctl --no-pager --full status "$SERVICE"
