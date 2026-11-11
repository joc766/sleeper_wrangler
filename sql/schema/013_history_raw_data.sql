-- +goose Up
ALTER TABLE PlayerHistory
ADD COLUMN jsondata TEXT DEFAULT NULL;

ALTER TABLE PlayerHistory
ADD COLUMN pointsnotds REAL DEFAULT NULL;

ALTER TABLE PlayerHistory
ADD COLUMN tdstats TEXT DEFAULT NULL;

-- +goose Down
ALTER TABLE PlayerHistory
DROP COLUMN tdstats;

ALTER TABLE PlayerHistory
DROP COLUMN pointsnotds;

ALTER TABLE PlayerHistory
DROP COLUMN jsondata;
