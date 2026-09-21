-- Illustrative queries from the original schema file; not migrations.

-- Regular season payout
SELECT
    l.Season,
    u.UserName,
    t.TeamName,
    COUNT(*) * 10 AS TotalReward
FROM WeeklyStats ws
    JOIN Team t ON ws.RosterCode = t.RosterCode AND ws.LeagueID = t.LeagueID
    JOIN User u ON t.UserID = u.UserID
    JOIN League l ON ws.LeagueID = l.LeagueID
WHERE ws.Week <= 14
    AND ws.Win = 1
    AND l.Season = '2024'
    AND ws.IsPlayoff = 0
GROUP BY l.Season, u.UserName, t.TeamName
ORDER BY TotalReward DESC;

-- Win streaks
WITH WinStreaks AS (
    SELECT
        u.UserName,
        l.Season,
        ws.Week,
        ws.Win,
        ROW_NUMBER() OVER (PARTITION BY u.UserName ORDER BY l.Season, ws.Week)
            - ROW_NUMBER() OVER (PARTITION BY u.UserName, ws.Win ORDER BY l.Season, ws.Week) AS win_group
    FROM WeeklyStats ws
        JOIN Team t ON ws.RosterCode = t.RosterCode
        JOIN User u ON t.UserID = u.UserID
        JOIN League l ON ws.LeagueID = l.LeagueID
    WHERE ws.Win = 1
)
SELECT
    UserName,
    Season,
    MIN(Week) AS start_week,
    MAX(Week) AS end_week,
    COUNT(*) AS streak_length
FROM WinStreaks
GROUP BY UserName, Season, win_group
ORDER BY streak_length DESC;

-- Point totals
SELECT
    ROW_NUMBER() OVER (ORDER BY mr1.Points + mr2.Points DESC) AS Rank,
    l.Season,
    mr1.Week,
    u1.UserName AS 'Player 1',
    mr1.Points,
    u2.UserName AS 'Player 2',
    mr2.Points,
    mr1.Points + mr2.Points AS 'Total Points'
FROM MatchupRoster mr1
    JOIN MatchupRoster mr2 ON mr1.MatchupID = mr2.MatchupID AND mr1.Points > mr2.Points
    JOIN Team t1 ON mr1.RosterCode = t1.RosterCode
    JOIN Team t2 ON mr2.RosterCode = t2.RosterCode
    JOIN User u1 ON t1.UserID = u1.UserID
    JOIN User u2 ON t2.UserID = u2.UserID
    JOIN League l ON mr1.LeagueID = l.LeagueID
ORDER BY mr1.Points + mr2.Points DESC;
