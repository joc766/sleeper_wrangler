-- +goose Up
CREATE TABLE Draft (
  DraftID TEXT PRIMARY KEY,
  LeagueID TEXT NOT NULL,
  Season TEXT NOT NULL,
  Type TEXT, -- 'snake', 'linear', 'auction'
  Status TEXT, -- 'pre_draft', 'in_progress', 'complete'
  StartTime DATETIME,
  EndTime DATETIME,
  Settings TEXT, -- JSON for draft settings
  JSONData TEXT,
  UNIQUE (LeagueID, Season),
  FOREIGN KEY (LeagueID) REFERENCES League (LeagueID)
);

CREATE TABLE DraftPick (
  DraftPickID INTEGER PRIMARY KEY AUTOINCREMENT,
  DraftID TEXT NOT NULL,
  LeagueID TEXT NOT NULL, -- Denormalized
  Season TEXT NOT NULL, -- Denormalized
  Round INTEGER NOT NULL,
  Pick INTEGER NOT NULL,
  RosterCode INTEGER NOT NULL,
  PlayerID TEXT NOT NULL,
  PickTime DATETIME,
  JSONData TEXT,
  UNIQUE (DraftID, Round, Pick),
  FOREIGN KEY (DraftID) REFERENCES Draft (DraftID),
  FOREIGN KEY (PlayerID) REFERENCES Player (PlayerID)
);

CREATE INDEX idx_draft_season_status ON Draft (Season, Status);

CREATE INDEX idx_draft_pick_league_season_roster ON DraftPick (LeagueID, Season, RosterCode);

CREATE INDEX idx_draft_pick_player_season ON DraftPick (PlayerID, Season);

-- +goose Down
DROP TABLE DraftPick;

DROP TABLE Draft;
