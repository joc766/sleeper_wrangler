import sqlite3
from typing import NamedTuple


class InsertMatchupParms(NamedTuple):
    LeagueID: str
    Season: str
    Week: int
    MatchupCode: int
    PlayoffRound: int | None
    IsPlayoff: int | None = 0
    JSONData: str | None = None


class InsertMatchupRosterParms(NamedTuple):
    MatchupID: int
    RosterID: int
    RosterCode: int
    LeagueID: str
    Season: str
    Week: int
    Points: float
    IsWinner: int | None = None
    JSONData: str | None = None


class Matchup(NamedTuple):
    MatchupID: int
    LeagueID: str
    Season: str
    Week: int
    MatchupCode: int
    PlayoffRound: int
    IsPlayoff: int
    JSONData: str

    @classmethod
    def from_row(cls, row: sqlite3.Row):
        return cls(**dict(row))


def insert_matchups(conn: sqlite3.Connection, data: list[InsertMatchupParms]):
    matchup_qry = """
        INSERT OR REPLACE INTO Matchup (LeagueID, Season, Week, MatchupCode, PlayoffRound, IsPlayoff, JSONData)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    with conn:
        conn.executemany(matchup_qry, data)


def select_matchups(conn: sqlite3.Connection, league_id: str):
    matchup_qry = """
    SELECT MatchupID, LeagueID, Season, Week, MatchupCode, PlayoffRound, IsPlayoff, JSONData
    FROM Matchup WHERE LeagueID = ?;
    """
    return [
        Matchup.from_row(m) for m in conn.execute(matchup_qry, (league_id,)).fetchall()
    ]


def insert_matchup_rosters(
    conn: sqlite3.Connection, data: list[InsertMatchupRosterParms]
):
    matchup_roster_qry = """
        INSERT OR REPLACE INTO MatchupRoster (MatchupID, RosterID, RosterCode, LeagueID, Season, Week, Points, IsWinner, JSONData)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    with conn:
        conn.executemany(matchup_roster_qry, data)
