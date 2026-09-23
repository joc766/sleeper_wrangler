-- +goose Up
CREATE TABLE Player (
  PlayerID TEXT PRIMARY KEY,
  FirstName TEXT,
  LastName TEXT,
  FullName TEXT NOT NULL, -- Computed column for performance
  Team TEXT,
  Position TEXT NOT NULL,
  Status TEXT, -- 'Active', 'Injured', 'Suspended', etc.
  InjuryStatus TEXT,
  Age INTEGER,
  Height TEXT,
  Weight INTEGER,
  College TEXT,
  YearsExp INTEGER,
  SearchRank INTEGER, -- For ADP calculations
  JSONData TEXT
);

CREATE INDEX idx_player_fullname ON Player (FullName);

CREATE INDEX idx_player_position_team ON Player (Position, Team);

CREATE INDEX idx_player_position_searchrank ON Player (Position, SearchRank);

CREATE INDEX idx_player_status ON Player (Status);

-- +goose StatementBegin
CREATE TRIGGER update_player_fullname AFTER
UPDATE OF FirstName,
LastName ON Player BEGIN
UPDATE Player
SET
  FullName = TRIM(
    COALESCE(FirstName, '') || ' ' || COALESCE(LastName, '')
  )
WHERE
  PlayerID = NEW.PlayerID;

END;

-- +goose StatementEnd
-- +goose Down
DROP TRIGGER update_player_fullname;

DROP TABLE Player;
