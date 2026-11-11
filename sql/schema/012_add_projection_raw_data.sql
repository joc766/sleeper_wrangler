-- +goose Up
ALTER TABLE Projections
ADD COLUMN jsondata TEXT DEFAULT NULL;

ALTER TABLE Projections
ADD COLUMN pointsnotds REAL DEFAULT NULL;

ALTER TABLE Projections
ADD COLUMN tdstats TEXT DEFAULT NULL;

-- +goose Down
ALTER TABLE Projections
DROP COLUMN tdstats;

ALTER TABLE Projections
DROP COLUMN pointsnotds;

ALTER TABLE Projections
DROP COLUMN jsondata;
