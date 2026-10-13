-- name: GetLeagueIDBySeason :one
SELECT
  LeagueID
FROM
  League
WHERE
  Season = ?;

-- name: GetLeagueScoringSettings :one
SELECT
  ScoringSettings
FROM
  League
WHERE
  LeagueID = ?;
