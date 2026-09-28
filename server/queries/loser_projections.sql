-- name: GetLatestProjection :one
SELECT
  ProjectionData,
  CreatedAt,
  GameStatus
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
  LoserProjections (ProjectionData, CreatedAt, GameStatus)
VALUES
  (?, CURRENT_TIMESTAMP, ?);
