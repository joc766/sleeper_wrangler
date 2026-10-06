-- name: GetLatestProjection :one
SELECT
  ProjectionData,
  CreatedAt,
  GameStatus,
  Week
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
  LoserProjections (ProjectionData, CreatedAt, GameStatus, Week)
VALUES
  (?, CURRENT_TIMESTAMP, ?, ?);
