import sqlite3
from typing import NamedTuple


class PlayerHistory(NamedTuple):
    PlayerID: str
    Season: str
    Week: str
    PtsHalfPPR: float | None
    JSONData: str | None
    PointsNoTDs: float | None
    TDStats: str | None


def upsert_player_history(conn: sqlite3.Connection, data: list[PlayerHistory]):
    with conn:
        history_query = """
                INSERT INTO PlayerHistory (PlayerID, Season, Week, PtsHalfPPR, JSONData, PointsNoTDs, TDStats)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (PlayerID, Season, Week)
                DO UPDATE SET
                    PtsHalfPPR = excluded.PtsHalfPPR,
                    JSONData = excluded.JSONData,
                    PointsNoTDs = excluded.PointsNoTDs,
                    TDStats = excluded.TDStats
            """
        conn.executemany(history_query, data)
