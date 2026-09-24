import sqlite3
from typing import NamedTuple


class Roster(NamedTuple):
    RosterID: int
    RosterCode: int

    @classmethod
    def from_row(cls, row: sqlite3.Row):
        return Roster(**dict(row))


class CreateRosterParms(NamedTuple):
    UserID: int
    RosterCode: int
    LeagueID: str
    Season: str
    TeamName: str
    Record: str
    Streak: int
    Fpts: float
    FptsAgainst: float
    Wins: int
    Losses: int
    Ties: int
    JSONData: str | None = None


def select_rosters(conn: sqlite3.Connection, league_id: str):
    roster_qry = "SELECT RosterID, RosterCode FROM Roster WHERE LeagueID = ?;"
    return [
        Roster.from_row(row)
        for row in conn.execute(roster_qry, (league_id,)).fetchall()
    ]


def create_rosters(conn: sqlite3.Connection, roster_data: list[CreateRosterParms]):
    teams_qry = """
        INSERT OR REPLACE INTO Roster (UserID, RosterCode, LeagueID, Season, TeamName, Record, Streak, Fpts, FptsAgainst, Wins, Losses, Ties, JSONData)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    with conn:
        conn.executemany(teams_qry, roster_data)
