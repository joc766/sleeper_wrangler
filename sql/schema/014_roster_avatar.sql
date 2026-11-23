-- +goose Up
ALTER TABLE Roster ADD COLUMN TeamAvatar TEXT;

-- +goose Down
ALTER TABLE Roster DROP COLUMN TeamAvatar;
