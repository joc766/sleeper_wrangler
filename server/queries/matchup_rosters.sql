-- name: GetStarters :many
SELECT
  RosterCode,
  CAST(JSONData -> '$.starters' AS TEXT) AS 'Starters',
  Points
FROM
  MatchupRoster
WHERE
  LeagueID = ?
  AND Week = ?;
