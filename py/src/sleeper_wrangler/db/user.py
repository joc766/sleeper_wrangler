import sqlite3
from typing import NamedTuple


class CreateUsersParms(NamedTuple):
    UserID: str
    UserName: str
    DisplayName: str
    Avatar: str | None = None
    JSONData: str | None = None


def create_users(conn: sqlite3.Connection, users: list[CreateUsersParms]):
    user_qry = """
        INSERT INTO User (UserID, UserName, DisplayName, Avatar, JSONData)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT (UserID)
        DO UPDATE SET Avatar = excluded.Avatar,
        JSONData = excluded.JSONData
    """
    with conn:
        conn.executemany(user_qry, users)
