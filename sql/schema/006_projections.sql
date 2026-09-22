-- +goose Up
create table Projections (
  ProjectionID INTEGER PRIMARY KEY AUTOINCREMENT,
  Date DATE NOT NULL,
  Season TEXT NOT NULL,
  Week INTEGER NOT NULL,
  PlayerID TEXT NOT NULL,
  InjuryStatus TEXT NULL,
  PointsHalfPPR REAL, -- ok with floating point for now, could convert to hundredths of pts
  FOREIGN KEY (PlayerID) REFERENCES Player (PlayerID)
);

CREATE INDEX idx_projection_week_player_season ON Projections (Season, Week, PlayerID);

-- +goose Down
DROP TABLE Projections;
