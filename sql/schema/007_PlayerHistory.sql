-- +goose up
CREATE TABLE PlayerHistory (
  PlayerHistoryID INTEGER PRIMARY KEY AUTOINCREMENT,
  PlayerID TEXT NOT NULL,
  Season TEXT NOT NULL,
  Week INT NOT NULL,
  PtsHalfPPR REAL,
  UNIQUE (PlayerID, Season, Week),
  FOREIGN KEY (PlayerID) REFERENCES Player (PlayerID)
);

CREATE INDEX idx_playerhistory_player ON PlayerHistory (PlayerID);

-- +goose down
DROP TABLE PlayerHistory;
