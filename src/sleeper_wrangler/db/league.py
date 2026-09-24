import sqlite3
from typing import NamedTuple


class InsertLeagueParms(NamedTuple):
    LeagueID: str
    Season: str
    Name: str
    Status: str
    ScoringSettings: str
    RosterPositions: str
    Previous_League_ID: str | None
    DraftID: str | None
    Settings: str
    JSONData: str | None


def create_league(conn: sqlite3.Connection, data: InsertLeagueParms):
    with conn:
        league_qry = """
            INSERT OR REPLACE INTO League (LeagueID, Season, Name, Previous_League_ID, DraftID, Status, Settings, ScoringSettings, RosterPositions, JSONData)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        conn.execute(league_qry, data)


def select_league_season(conn: sqlite3.Connection, league_id: str):
    return conn.execute(
        "SELECT Season FROM League WHERE LeagueID = ?", (league_id,)
    ).fetchone()["Season"]
