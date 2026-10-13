-- name: GetMatchupPlayers :many
SELECT
  PlayerID
FROM
  MatchupRoster mr
  JOIN MatchupRosterPlayer mrp ON mr.MatchupRosterID = mrp.MatchupRosterID
WHERE
  mr.LeagueID = ?
  AND mr.Week = ?
  AND mrp.Starter = 1;
