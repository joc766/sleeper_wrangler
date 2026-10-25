-- +goose Up
CREATE TABLE MasterLeague (MasterLeagueID INTEGER PRIMARY KEY);

ALTER TABLE League
ADD COLUMN MasterLeagueID INTEGER REFERENCES MasterLeague (MasterLeagueID) DEFAULT NULL;

CREATE INDEX idx_league_master_league ON League (MasterLeagueID);

-- +goose Down
DROP TABLE MasterLeague;

ALTER TABLE League
DROP COLUMN MasterLeagueID;
