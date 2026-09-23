-- +goose Up
CREATE TABLE User (
  UserID TEXT PRIMARY KEY,
  UserName TEXT NOT NULL,
  DisplayName TEXT,
  Avatar TEXT,
  JSONData TEXT,
  UNIQUE (UserName)
);

CREATE TABLE League (
  LeagueID TEXT PRIMARY KEY,
  Season TEXT NOT NULL,
  Name TEXT NOT NULL,
  Previous_League_ID TEXT,
  DraftID TEXT,
  Status TEXT, -- 'in_season', 'complete', 'drafting', etc.
  Settings TEXT, -- JSON for league settings
  ScoringSettings TEXT, -- JSON for scoring rules
  RosterPositions TEXT, -- JSON for roster requirements
  JSONData TEXT
);

CREATE TABLE Team (
  TeamID INTEGER PRIMARY KEY AUTOINCREMENT,
  RosterCode INTEGER NOT NULL,
  UserID TEXT NOT NULL,
  LeagueID TEXT NOT NULL,
  Season TEXT NOT NULL, -- Denormalized for performance
  TeamName TEXT,
  Record TEXT,
  Streak TEXT,
  Fpts REAL DEFAULT 0,
  FptsAgainst REAL DEFAULT 0,
  Wins INTEGER DEFAULT 0,
  Losses INTEGER DEFAULT 0,
  Ties INTEGER DEFAULT 0,
  JSONData TEXT,
  UNIQUE (UserID, LeagueID),
  UNIQUE (LeagueID, Season, RosterCode),
  FOREIGN KEY (UserID) REFERENCES User (UserID),
  FOREIGN KEY (LeagueID) REFERENCES League (LeagueID)
);

CREATE INDEX idx_league_season_status ON League (Season, Status);

CREATE INDEX idx_league_previous ON League (Previous_League_ID);

CREATE INDEX idx_team_league_season ON Team (LeagueID, Season);

CREATE INDEX idx_team_season_points ON Team (Season, Fpts);

-- +goose Down
-- Dropping tables also removes their indexes.
DROP TABLE Team;

DROP TABLE League;

DROP TABLE User;
