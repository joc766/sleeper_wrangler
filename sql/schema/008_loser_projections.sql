-- +goose Up
CREATE TABLE LoserProjections (
  LoserProjectionID INTEGER PRIMARY KEY AUTOINCREMENT,
  ProjectionData TEXT NOT NULL,
  CreatedAt TEXT NOT NULL,
  GameStatus TEXT NULL
);

-- +goose Down
DROP TABLE LoserProjections;
