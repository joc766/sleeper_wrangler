# Sleeper Wrangler

Pull fantasy football league data from the Sleeper API into SQLite.
The loader lives in `src/sleeper_wrangler/get_data.py`.

## Database migrations

The schema is managed by [Goose](https://github.com/pressly/goose) SQL migrations
in `sql/schema/`. Install the Goose CLI on macOS with:

```sh
brew install goose
```

From the repository root, configure Goose to use the same database as the loader
(the loader currently sets `db_path` in `get_data.py`; adjust both paths together):

```sh
export GOOSE_DRIVER=sqlite3
export GOOSE_DBSTRING="$HOME/.local/share/sleeper/db.sqlite3"
export GOOSE_MIGRATION_DIR=./sql/schema
mkdir -p "$(dirname "$GOOSE_DBSTRING")"
```

For a **new, empty database**, apply the migrations before running the loader:

```sh
goose up
goose status
```

Goose records applied versions in `goose_db_version`, so subsequent `goose up`
runs apply only pending migrations. Each migration runs in a transaction.

### Migration layout

| Version | Contents |
| --- | --- |
| `00001_create_core_entities.sql` | User, League, Team, and their indexes |
| `00002_create_players.sql` | Player, its indexes, and the full-name trigger |
| `00003_create_matchups.sql` | Matchup, MatchupRoster, MatchupRosterPlayer, and their indexes |
| `00004_create_statistics.sql` | WeeklyStats, SeasonStats, their indexes, and the timestamp trigger |
| `00005_create_drafts.sql` | Draft, DraftPick, and their indexes |

Dependencies are created first and dropped last. Every file has `-- +goose Up`
and `-- +goose Down` sections. Triggers use `-- +goose StatementBegin` and
`-- +goose StatementEnd` so Goose treats their internal semicolons as part of
one statement. Dropping a table also drops its indexes.

The original illustrative queries are kept separately in `sql/examples.sql`.

### Existing databases

These five migrations reproduce the former `schema.sql`; they initialize a
database rather than upgrade a different legacy schema. A normal `goose up`
against an unversioned database with existing tables will fail with
"table already exists".

- If the data can be reloaded, point Goose and the loader at a new database,
  run `goose up`, and reload from Sleeper.
- To keep an existing database, back it up and compare its tables, columns,
  constraints, indexes, and triggers against a fresh database created by these
  migrations. **Only if the schemas match and no migrations have been recorded**,
  initialize Goose's tracking table and record these five versions as applied:

  ```sh
  goose status
  sqlite3 "$GOOSE_DBSTRING" <<'SQL'
  BEGIN;
  INSERT INTO goose_db_version (version_id, is_applied)
  VALUES (1, 1), (2, 1), (3, 1), (4, 1), (5, 1);
  COMMIT;
  SQL
  goose status
  ```

  If the schema differs (including databases built from `sql/old/`), reconcile
  those differences before baselining; recording a version does not change the
  actual schema.

### Future changes and rollbacks

Create a new numbered migration rather than editing an already-applied file:

```sh
goose -s create add_player_birth_date sql
```

Fill in its `Up` and `Down` sections, then run `goose up`. To roll back the most
recent migration, use `goose down`; `goose down-to 0` rolls back everything.
The initial migrations' rollbacks drop tables and their data, so use these
commands only when that data loss is intended.
