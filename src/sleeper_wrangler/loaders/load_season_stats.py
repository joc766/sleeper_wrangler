import sqlite3


def calculate_season_stats(conn: sqlite3.Connection, league_id: str):
    """
    Calculate and insert season stats from weekly stats.
    """
    season = conn.execute(
        "SELECT Season FROM League WHERE LeagueID = ?", (league_id,)
    ).fetchone()["Season"]
    # Get aggregated stats for each roster
    season_data = conn.execute(
        """
        SELECT
            RosterCode,
            SUM(Points) as TotalPoints,
            SUM(PointsAgainst) as TotalPointsAgainst,
            SUM(Win) as Wins,
            SUM(Loss) as Losses,
            SUM(Tie) as Ties,
            SUM(CASE WHEN IsPlayoff = 0 THEN Win ELSE 0 END) as RegularSeasonWins,
            SUM(CASE WHEN IsPlayoff = 0 THEN Loss ELSE 0 END) as RegularSeasonLosses,
            SUM(CASE WHEN IsPlayoff = 1 THEN Win ELSE 0 END) as PlayoffWins,
            SUM(CASE WHEN IsPlayoff = 1 THEN Loss ELSE 0 END) as PlayoffLosses,
            COUNT(*) as GamesPlayed
        FROM WeeklyStats
        WHERE LeagueID = ? AND Season = ?
        GROUP BY RosterCode
    """,
        (league_id, season),
    ).fetchall()

    # Calculate derived stats and insert
    season_stats_qry = """
        INSERT OR REPLACE INTO SeasonStats (RosterCode, LeagueID, Season, TotalPoints, TotalPointsAgainst, Wins, Losses, Ties, WinPercentage, PointsPerGame, PointsAgainstPerGame, PointDifferential, RegularSeasonWins, RegularSeasonLosses, PlayoffWins, PlayoffLosses)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    stats_data = []
    for row in season_data:
        (
            roster_code,
            total_points,
            total_against,
            wins,
            losses,
            ties,
            reg_wins,
            reg_losses,
            playoff_wins,
            playoff_losses,
            games,
        ) = row

        if games > 0:
            win_pct = (wins + 0.5 * ties) / games if games > 0 else 0
            points_per_game = total_points / games
            points_against_per_game = total_against / games
            point_diff = total_points - total_against
        else:
            win_pct = 0
            points_per_game = 0
            points_against_per_game = 0
            point_diff = 0

        stats_data.append(
            (
                roster_code,
                league_id,
                season,
                total_points,
                total_against,
                wins,
                losses,
                ties,
                win_pct,
                points_per_game,
                points_against_per_game,
                point_diff,
                reg_wins,
                reg_losses,
                playoff_wins,
                playoff_losses,
            )
        )

    if stats_data:
        conn.executemany(season_stats_qry, stats_data)
