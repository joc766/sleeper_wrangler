import sqlite3
from typing import NamedTuple


class CreateUsersParms(NamedTuple):
    UserID: str
    UserName: str
    DisplayName: str
    JSONData: str
    Avatar: str | None = None


def create_users(conn: sqlite3.Connection, users: list[CreateUsersParms]):
    user_qry = """
        INSERT OR REPLACE INTO User (UserID, UserName, DisplayName, Avatar, JSONData)
        VALUES (?, ?, ?, ?, ?)
    """
    with conn:
        conn.executemany(user_qry, users)
