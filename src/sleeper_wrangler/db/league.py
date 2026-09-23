import sqlite3


def select_league_season(conn: sqlite3.Connection, league_id: str):
    return conn.execute(
        "SELECT Season FROM League WHERE LeagueID = ?", (league_id,)
    ).fetchone()["Season"]
