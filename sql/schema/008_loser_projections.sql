-- +goose up
CREATE TABLE LoserProjections (
  LoserProjectionID INTEGER PRIMARY KEY AUTOINCREMENT,
  ProjectionData TEXT NOT NULL,
  CreatedAt TEXT NOT NULL
);

-- +goose down
DROP TABLE LoserProjections;
