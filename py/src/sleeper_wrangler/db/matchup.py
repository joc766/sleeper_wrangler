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
    RosterID: int | None
    RosterCode: int
    LeagueID: str
    Season: str
    Week: int
    Points: float
    IsWinner: int | None = None
    JSONData: str | None = None


class InsertMRPlayerParms(NamedTuple):
    MatchupRosterID: int
    PlayerID: str
    Position: str
    Starter: int
    Points: float | None
    ProjectedPoints: float | None
    JSONData: str | None


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
        INSERT INTO Matchup (LeagueID, Season, Week, MatchupCode, PlayoffRound, IsPlayoff, JSONData)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (LeagueID, Season, Week, MatchupCode)
        DO UPDATE SET
            JSONData = excluded.JSONData;
    """
    with conn:
        conn.executemany(matchup_qry, data)


def select_matchups(conn: sqlite3.Connection, league_id: str, week: int):
    matchup_qry = """
    SELECT MatchupID, LeagueID, Season, Week, MatchupCode, PlayoffRound, IsPlayoff, JSONData
    FROM Matchup WHERE LeagueID = ? AND Week = ?;
    """
    return [
        Matchup.from_row(m)
        for m in conn.execute(matchup_qry, (league_id, week)).fetchall()
    ]


def select_matchup_rosters(conn: sqlite3.Connection, league_id: str, week: int):
    matchup_roster_qry = """
        SELECT MatchupRosterID, JSONData FROM MatchupRoster WHERE LeagueID = ? AND Week = ?;
    """
    with conn:
        return conn.execute(matchup_roster_qry, (league_id, week)).fetchall()


def insert_matchup_rosters(
    conn: sqlite3.Connection, data: list[InsertMatchupRosterParms]
):
    matchup_roster_qry = """
        INSERT INTO MatchupRoster (MatchupID, RosterID, RosterCode, LeagueID, Season, Week, Points, IsWinner, JSONData)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (MatchupID, RosterCode)
        DO UPDATE SET
            Points = excluded.Points,
            IsWinner = excluded.IsWinner,
            JSONData = excluded.JSONData;

    """
    with conn:
        conn.executemany(matchup_roster_qry, data)


def refresh_mr_players(
    conn: sqlite3.Connection,
    mr_players: list[InsertMRPlayerParms],
):
    if len(mr_players) == 0:
        return

    with conn:
        conn.execute("""
                    CREATE TEMP TABLE IF NOT EXISTS refreshed_players (
                        matchup_roster_id INTEGER,
                        player_id TEXT,
                        PRIMARY KEY (matchup_roster_id, player_id)
                    )
                """)
        conn.execute("""DELETE FROM refreshed_players""")

        conn.executemany(
            """
                INSERT INTO refreshed_players (matchup_roster_id, player_id)
                VALUES (?, ?)
            """,
            [(p.MatchupRosterID, p.PlayerID) for p in mr_players],
        )
        conn.executemany(
            """
                INSERT INTO MatchupRosterPlayer (MatchupRosterID, PlayerID, Position, Starter, Points, ProjectedPoints, JSONData)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (MatchupRosterID, PlayerID)
                DO UPDATE SET
                    Position = excluded.Position,
                    Starter = excluded.Starter,
                    Points = excluded.Points,
                    ProjectedPoints = excluded.ProjectedPoints,
                    JSONData = excluded.JSONData
            """,
            mr_players,
        )
        conn.execute(
            """
                DELETE FROM MatchupRosterPlayer AS mrp
                WHERE mrp.MatchupRosterID IN (
                    SELECT matchup_roster_id
                    FROM refreshed_players
                )
                AND NOT EXISTS (
                    SELECT 1
                    FROM refreshed_players AS r
                    WHERE r.player_id = mrp.PlayerID
                        AND r.matchup_roster_id = mrp.MatchupRosterID
                )
            """
        )
