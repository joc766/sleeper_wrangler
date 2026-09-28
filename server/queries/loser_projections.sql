-- name: GetLatestProjection :one
SELECT
  ProjectionData,
  CreatedAt
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
  LoserProjections (ProjectionData, CreatedAt)
VALUES
  (?, CURRENT_TIMESTAMP);
