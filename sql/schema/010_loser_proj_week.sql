-- +goose Up
ALTER TABLE LoserProjections
ADD COLUMN week INTEGER DEFAULT NULL;

ALTER TABLE LoserProjections
ADD COLUMN season TEXT DEFAULT NULL;

-- +goose Down
ALTER TABLE LoserProjections
DROP COLUMN week;

ALTER TABLE LoserProjections
DROP COLUMN season;
