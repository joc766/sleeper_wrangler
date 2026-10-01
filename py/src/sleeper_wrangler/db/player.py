import sqlite3
from typing import NamedTuple


class CreatePlayerParams(NamedTuple):
    PlayerID: str
    FirstName: str | None
    LastName: str | None
    FullName: str
    Team: str | None
    Position: str
    Status: str | None
    InjuryStatus: str | None
    Age: int | None
    Height: str | None
    Weight: int | None
    College: str | None
    YearsExp: int | None
    SearchRank: int | None
    JSONData: str | None


def select_player_positions(conn: sqlite3.Connection):
    players_query = """
        SELECT PlayerID, Position FROM Player;
    """
    with conn:
        return conn.execute(players_query).fetchall()


def create_players(conn: sqlite3.Connection, data: list[CreatePlayerParams]):
    player_qry = """
        INSERT INTO Player (PlayerID, FirstName, LastName, FullName, Team, Position, Status, InjuryStatus, Age, Height, Weight, College, YearsExp, SearchRank, JSONData)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (PlayerID)
        DO UPDATE SET
            FirstName = excluded.FirstName,
            LastName = excluded.LastName,
            FullName = excluded.FullName,
            Team = excluded.Team,
            Position = excluded.Position,
            Status = excluded.Status,
            InjuryStatus = excluded.InjuryStatus,
            Age = excluded.Age,
            Height = excluded.Height,
            Weight = excluded.Weight,
            College = excluded.College,
            YearsExp = excluded.YearsExp,
            SearchRank = excluded.SearchRank,
            JSONData = excluded.JSONData
    """
    with conn:
        conn.executemany(player_qry, data)
