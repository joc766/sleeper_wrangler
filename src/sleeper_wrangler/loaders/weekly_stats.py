import sqlite3

from sleeper_wrangler.db.league import select_league_season


def calculate_weekly_stats(conn: sqlite3.Connection, league_id: str):
    """
    Calculate and insert weekly stats from matchup data.
    """
    season = select_league_season(conn, league_id)
    # Get all matchup roster data for this league/season
    weekly_data = conn.execute(
        """
        SELECT mr.RosterCode, mr.Week, mr.Points, mr.IsWinner, m.IsPlayoff,
               mr2.Points as OpponentPoints, mr2.RosterCode as OpponentRosterCode
        FROM MatchupRoster mr
        JOIN Matchup m ON mr.MatchupID = m.MatchupID
        LEFT JOIN MatchupRoster mr2 ON mr.MatchupID = mr2.MatchupID AND mr.RosterCode != mr2.RosterCode
        WHERE mr.LeagueID = ? AND mr.Season = ?
        ORDER BY mr.RosterCode, mr.Week
    """,
        (league_id, season),
    ).fetchall()

    # Group by roster and week
    roster_week_stats = {}
    for row in weekly_data:
        roster_code, week, points, is_winner, is_playoff, opp_points, opp_roster = row
        key = (roster_code, week)

        if key not in roster_week_stats:
            roster_week_stats[key] = {
                "roster_code": roster_code,
                "week": week,
                "points": points or 0,
                "points_against": opp_points or 0,
                "win": is_winner or 0,
                "loss": 1 - (is_winner or 0) if points is not None else 0,
                "tie": 0,  # Sleeper doesn't support ties typically
                "opponent_roster": opp_roster,
                "is_playoff": is_playoff or 0,
            }

    # Insert weekly stats
    weekly_stats_qry = """
        INSERT OR REPLACE INTO WeeklyStats (RosterCode, LeagueID, Season, Week, Points, PointsAgainst, Win, Loss, Tie, OpponentRosterCode, IsPlayoff)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    stats_data = []
    for stats in roster_week_stats.values():
        stats_data.append(
            (
                stats["roster_code"],
                league_id,
                season,
                stats["week"],
                stats["points"],
                stats["points_against"],
                stats["win"],
                stats["loss"],
                stats["tie"],
                stats["opponent_roster"],
                stats["is_playoff"],
            )
        )

    if stats_data:
        conn.executemany(weekly_stats_qry, stats_data)
