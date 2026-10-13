-- name: GetProjections :many
SELECT
  PlayerID,
  PointsHalfPPR
FROM
  Projections
WHERE
  Season = ?
  AND Week = ?
  AND PlayerID IN (sqlc.slice ('player_ids'));

-- name: UpsertProjection :exec
INSERT INTO Projections (Date, Season, Week, PlayerID, InjuryStatus, PointsHalfPPR)
VALUES (?, ?, ?, ?, ?, ?)
ON CONFLICT (Season, Week, PlayerID)
DO UPDATE SET
  Date = excluded.Date,
  InjuryStatus = excluded.InjuryStatus,
  PointsHalfPPR = excluded.PointsHalfPPR;
