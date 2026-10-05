-- +goose up
CREATE TABLE Autosubs (
  AutosubID INTEGER PRIMARY KEY AUTOINCREMENT,
  LeagueID TEXT NOT NULL,
  Week INTEGER NOT NULL,
  PlayerID TEXT NOT NULL,
  SubstitutePlayerID TEXT NOT NULL,
  FOREIGN KEY (PlayerID) REFERENCES Player (PlayerID),
  FOREIGN KEY (LeagueID) REFERENCES League (LeagueID),
  FOREIGN KEY (SubstitutePlayerID) REFERENCES Player (PlayerID)
);

-- +goose down
DROP TABLE Autosubs;
