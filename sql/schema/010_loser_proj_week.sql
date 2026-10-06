-- +goose Up
ALTER TABLE LoserProjections
ADD COLUMN week INTEGER DEFAULT NULL;

-- +goose Down
ALTER TABLE LoserProjections
DROP COLUMN week;
