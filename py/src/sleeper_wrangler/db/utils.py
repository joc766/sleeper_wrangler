import sqlite3


def select_teams_and_starters(conn: sqlite3.Connection, season: str, week: int):
    with conn:
        return conn.execute(
            """
            SELECT
                u.UserName,
                r.TeamName,
                mr.MatchupRosterID,
                CASE
                    WHEN (orig_proj.PointsHalfPPR IS NULL OR orig_proj.PointsHalfPPR = 0)
                        AND subs.SubstitutePlayerID IS NOT NULL
                        THEN sub.PlayerID
                    ELSE p.PlayerID
                END AS PlayerID,
                CASE
                    WHEN (orig_proj.PointsHalfPPR IS NULL OR orig_proj.PointsHalfPPR = 0)
                        AND subs.SubstitutePlayerID IS NOT NULL
                        THEN sub.Team
                    ELSE p.Team
                END AS PlayerTeam,
                CASE
                    WHEN (orig_proj.PointsHalfPPR IS NULL OR orig_proj.PointsHalfPPR = 0)
                        AND subs.SubstitutePlayerID IS NOT NULL
                        THEN sub.Position
                    ELSE p.Position
                END AS Position,
                CASE
                    WHEN (orig_proj.PointsHalfPPR IS NULL OR orig_proj.PointsHalfPPR = 0)
                        AND subs.SubstitutePlayerID IS NOT NULL
                        THEN sub_mrp.Points
                    ELSE mrp.Points
                END AS CurrentPoints,
                CASE
                    WHEN (orig_proj.PointsHalfPPR IS NULL OR orig_proj.PointsHalfPPR = 0)
                        AND subs.SubstitutePlayerID IS NOT NULL
                        THEN sub_proj.PointsHalfPPR
                    ELSE orig_proj.PointsHalfPPR
                END AS ProjectedPoints
            FROM User AS u
                JOIN Roster AS r on r.UserID = u.UserID
                JOIN League AS l on r.LeagueID = l.LeagueID
                JOIN MatchupRoster AS mr ON mr.RosterCode = r.RosterCode and mr.Season = r.Season and mr.LeagueID = r.LeagueID
                JOIN MatchupRosterPlayer AS mrp ON mrp.MatchupRosterID = mr.MatchupRosterID
                JOIN Player p ON mrp.PlayerID = p.PlayerID
                LEFT JOIN Projections AS orig_proj
                    ON orig_proj.PlayerID = mrp.PlayerID
                    AND orig_proj.Season = mr.Season
                    AND orig_proj.Week = mr.Week
                LEFT JOIN Autosubs AS subs
                    ON subs.LeagueID = mr.LeagueID
                    AND subs.Week = mr.Week
                    AND subs.PlayerID = mrp.PlayerID
                LEFT JOIN Player AS sub ON sub.PlayerID = subs.SubstitutePlayerID
                LEFT JOIN Projections as sub_proj
                    ON sub_proj.PlayerID = sub.PlayerID
                    AND sub_proj.Season = mr.Season
                    AND sub_proj.Week = mr.Week
                LEFT JOIN MatchupRosterPlayer sub_mrp
                    ON sub_mrp.MatchupRosterID = mr.MatchupRosterID
                    AND sub_mrp.PlayerID = sub.PlayerID
            WHERE l.Season = ?
            AND mr.Week = ?
            AND mrp.Starter = 1;
        """,
            (season, week),
        ).fetchall()


def select_historical_performances(conn: sqlite3.Connection, player_ids: list[str]):
    with conn:
        return conn.execute("""
            SELECT p.[Position], proj.PointsHalfPPR AS 'projected', ph.PtsHalfPPR AS 'actual', ph.PtsHalfPPR - proj.PointsHalfPPR AS 'error'
            FROM Projections proj
               	JOIN Player p ON proj.PlayerID = p.PlayerID
               	JOIN MatchupRoster mr ON proj.Season = mr.Season AND proj.Week = mr.Week
               	JOIN MatchupRosterPlayer mrp ON mr.MatchupRosterID = mrp.MatchupRosterID AND proj.PlayerID = mrp.PlayerID
               	JOIN PlayerHistory ph ON proj.Season = ph.Season AND proj.Week = ph.Week AND proj.PlayerID = ph.PlayerID
                WHERE ph.PtsHalfPPR IS NOT NULL
            AND proj.PointsHalfPPR IS NOT NULL
        """).fetchall()
