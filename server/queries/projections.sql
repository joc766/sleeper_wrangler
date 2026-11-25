-- name: GetProjections :many
SELECT
  PlayerID,
  CAST(COALESCE(InjuryStatus, '') AS TEXT) AS InjuryStatus,
  PointsHalfPPR,
  PointsNoTDs,
  TDStats
FROM
  Projections
WHERE
  Season = ?
  AND Week = ?
  AND PlayerID IN (sqlc.slice ('player_ids'));

-- name: GetPlayerInfo :many
SELECT
  PlayerID,
  FullName,
  Position,
  Team
FROM
  Player
WHERE
  PlayerID IN (sqlc.slice ('player_ids'));

-- name: UpsertProjection :exec
INSERT INTO Projections (Date, Season, Week, PlayerID, InjuryStatus, PointsHalfPPR, PointsNoTDs, TDStats)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT (Season, Week, PlayerID)
DO UPDATE SET
  Date = excluded.Date,
  InjuryStatus = excluded.InjuryStatus,
  PointsHalfPPR = excluded.PointsHalfPPR,
  PointsNoTDs = excluded.PointsNoTDs,
  TDStats = excluded.TDStats;
