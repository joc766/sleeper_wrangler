-- name: GetLoserTable :many
SELECT
  m.LeagueID,
  m.Season,
  m.Week,
  u.UserName,
  mr.Points as min_points,
  mr.MatchupRosterID
FROM
  MasterLeague ml
  JOIN League l on ml.MasterLeagueID = l.MasterLeagueID
  JOIN Matchup m on l.LeagueID = m.LeagueID
  JOIN MatchupRoster mr ON m.MatchupID = mr.MatchupID
  JOIN Roster r on mr.RosterID = r.RosterID
  JOIN User u on r.UserID = u.UserID
WHERE
  ml.MasterLeagueID = @master_league_id
  AND m.IsPlayoff = @count_playoff
  AND CAST(m.Season AS INTEGER) >= @track_start_season
  AND NOT (
    m.Season = @track_start_season
    AND m.Week <= @track_start_week
  )
  AND (
    m.Season != @current_season
    OR m.Week < @current_week
  )
GROUP BY
  mr.Season,
  mr.Week
HAVING
  mr.Points = min(mr.Points)
