-- name: GetLatestProjection :one
SELECT
  ProjectionData,
  CreatedAt,
  GameStatus,
  Week,
  Season
FROM
  LoserProjections
WHERE
  LoserProjectionID = (
    SELECT
      MAX(LoserProjectionID)
    FROM
      LoserProjections
  );

-- name: CreateLoserProjection :exec
INSERT INTO
  LoserProjections (
    ProjectionData,
    CreatedAt,
    GameStatus,
    Week,
    Season
  )
VALUES
  (?, CURRENT_TIMESTAMP, ?, ?, ?);
