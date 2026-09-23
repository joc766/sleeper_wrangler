-- +goose Up
CREATE TABLE WeeklyStats (
  WeeklyStatsID INTEGER PRIMARY KEY AUTOINCREMENT,
  RosterCode INTEGER NOT NULL,
  LeagueID TEXT NOT NULL,
  Season TEXT NOT NULL,
  Week INTEGER NOT NULL,
  Points REAL NOT NULL,
  PointsAgainst REAL NOT NULL,
  Win INTEGER NOT NULL, -- SQLite boolean
  Loss INTEGER NOT NULL, -- SQLite boolean
  Tie INTEGER NOT NULL, -- SQLite boolean
  OpponentRosterCode INTEGER,
  IsPlayoff INTEGER DEFAULT 0, -- SQLite boolean
  CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (RosterCode, Season, Week),
  FOREIGN KEY (LeagueID) REFERENCES League (LeagueID)
);

CREATE TABLE SeasonStats (
  SeasonStatsID INTEGER PRIMARY KEY AUTOINCREMENT,
  RosterCode INTEGER NOT NULL,
  LeagueID TEXT NOT NULL,
  Season TEXT NOT NULL,
  TotalPoints REAL NOT NULL,
  TotalPointsAgainst REAL NOT NULL,
  Wins INTEGER NOT NULL,
  Losses INTEGER NOT NULL,
  Ties INTEGER NOT NULL,
  WinPercentage REAL NOT NULL,
  PointsPerGame REAL NOT NULL,
  PointsAgainstPerGame REAL NOT NULL,
  PointDifferential REAL NOT NULL,
  RegularSeasonWins INTEGER NOT NULL,
  RegularSeasonLosses INTEGER NOT NULL,
  PlayoffWins INTEGER DEFAULT 0,
  PlayoffLosses INTEGER DEFAULT 0,
  FinalRank INTEGER,
  CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
  UpdatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (RosterCode, Season),
  FOREIGN KEY (LeagueID) REFERENCES League (LeagueID)
);

CREATE INDEX idx_weekly_stats_league_season_week ON WeeklyStats (LeagueID, Season, Week);

CREATE INDEX idx_weekly_stats_season_week_points ON WeeklyStats (Season, Week, Points);

CREATE INDEX idx_weekly_stats_season_week_wins ON WeeklyStats (Season, Week, Win);

CREATE INDEX idx_season_stats_league_season_rank ON SeasonStats (LeagueID, Season, FinalRank);

CREATE INDEX idx_season_stats_season_total_points ON SeasonStats (Season, TotalPoints);

CREATE INDEX idx_season_stats_season_win_pct ON SeasonStats (Season, WinPercentage);

-- +goose StatementBegin
CREATE TRIGGER update_season_stats_timestamp AFTER
UPDATE ON SeasonStats BEGIN
UPDATE SeasonStats
SET
  UpdatedDate = CURRENT_TIMESTAMP
WHERE
  SeasonStatsID = NEW.SeasonStatsID;

END;

-- +goose StatementEnd
-- +goose Down
DROP TRIGGER update_season_stats_timestamp;

DROP TABLE SeasonStats;

DROP TABLE WeeklyStats;
