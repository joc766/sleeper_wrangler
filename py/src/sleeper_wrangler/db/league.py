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
            INSERT INTO League (LeagueID, Season, Name, Status, ScoringSettings, RosterPositions, Previous_League_ID, DraftID, Settings, JSONData)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (LeagueID)
            DO UPDATE SET
                Season = excluded.Season,
                Name = excluded.Name,
                Status = excluded.Status,
                ScoringSettings = excluded.ScoringSettings,
                RosterPositions = excluded.RosterPositions,
                Previous_League_ID = excluded.Previous_League_ID,
                DraftID = excluded.DraftID,
                Settings = excluded.Settings,
                JSONData = excluded.JSONData
        """
        conn.execute(league_qry, data)


def select_league_season(conn: sqlite3.Connection, league_id: str):
    return conn.execute(
        "SELECT Season FROM League WHERE LeagueID = ?", (league_id,)
    ).fetchone()["Season"]


def select_leagueid_from_season(conn: sqlite3.Connection, season: str):
    return conn.execute(
        "SELECT LeagueID FROM League WHERE Season = ?", (season,)
    ).fetchone()["LeagueID"]


def select_league_scoring_settings(conn: sqlite3.Connection, league_id: str):
    return conn.execute(
        "SELECT ScoringSettings FROM League WHERE LeagueID = ?", (league_id,)
    ).fetchone()["ScoringSettings"]


def select_league_settings(conn: sqlite3.Connection, league_id: str):
    return conn.execute(
        "SELECT Settings FROM League WHERE LeagueID = ?", (league_id,)
    ).fetchone()["Settings"]
