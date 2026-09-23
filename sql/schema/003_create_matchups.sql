-- +goose Up
CREATE TABLE Matchup (
  MatchupID INTEGER PRIMARY KEY AUTOINCREMENT,
  LeagueID TEXT NOT NULL,
  Season TEXT NOT NULL, -- Denormalized for performance
  Week INTEGER NOT NULL,
  MatchupCode INTEGER NOT NULL, -- Original Sleeper matchup_id
  PlayoffRound INTEGER, -- For playoff matchups
  IsPlayoff INTEGER DEFAULT 0, -- SQLite boolean
  JSONData TEXT,
  UNIQUE (LeagueID, Season, Week, MatchupCode),
  FOREIGN KEY (LeagueID) REFERENCES League (LeagueID)
);

CREATE TABLE MatchupRoster (
  MatchupRosterID INTEGER PRIMARY KEY AUTOINCREMENT,
  MatchupID INTEGER NOT NULL,
  RosterCode INTEGER NOT NULL,
  LeagueID TEXT NOT NULL, -- Denormalized for performance
  Season TEXT NOT NULL, -- Denormalized for performance
  Week INTEGER NOT NULL, -- Denormalized for performance
  Points REAL DEFAULT 0,
  ProjectedPoints REAL,
  IsWinner INTEGER, -- Pre-calculated for performance (SQLite boolean)
  JSONData TEXT,
  UNIQUE (MatchupID, RosterCode),
  UNIQUE (LeagueID, Season, Week, RosterCode),
  FOREIGN KEY (MatchupID) REFERENCES Matchup (MatchupID),
  FOREIGN KEY (LeagueID) REFERENCES League (LeagueID)
);

CREATE TABLE MatchupRosterPlayer (
  MatchupRosterPlayerID INTEGER PRIMARY KEY AUTOINCREMENT,
  MatchupRosterID INTEGER NOT NULL,
  PlayerID TEXT NOT NULL,
  Position TEXT NOT NULL,
  Starter INTEGER NOT NULL DEFAULT 0, -- SQLite boolean
  Points REAL DEFAULT 0,
  ProjectedPoints REAL,
  JSONData TEXT,
  UNIQUE (MatchupRosterID, PlayerID),
  FOREIGN KEY (MatchupRosterID) REFERENCES MatchupRoster (MatchupRosterID),
  FOREIGN KEY (PlayerID) REFERENCES Player (PlayerID)
);

CREATE INDEX idx_matchup_league_week ON Matchup (LeagueID, Season, Week);

CREATE INDEX idx_matchup_season_week ON Matchup (Season, Week);

CREATE INDEX idx_matchup_roster_league_season_week ON MatchupRoster (LeagueID, Season, Week);

CREATE INDEX idx_matchup_roster_season_week_points ON MatchupRoster (Season, Week, Points);

CREATE INDEX idx_matchup_roster_roster_season_week ON MatchupRoster (RosterCode, Season, Week);

CREATE INDEX idx_matchup_roster_player_roster_position_starter ON MatchupRosterPlayer (MatchupRosterID, Position, Starter);

CREATE INDEX idx_matchup_roster_player_player_position ON MatchupRosterPlayer (PlayerID, Position);

-- +goose Down
DROP TABLE MatchupRosterPlayer;

DROP TABLE MatchupRoster;

DROP TABLE Matchup;
