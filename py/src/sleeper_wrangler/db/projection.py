import json
import sqlite3
from typing import NamedTuple


class ProjectionData(NamedTuple):
    Date: str | None
    Season: str
    Week: int
    PlayerID: str
    InjuryStatus: str | None
    PointsHalfPPR: float | None
    JSONData: str | None
    PointsNoTDs: float | None
    TDStats: str | None

    @classmethod
    def from_json(cls, data: dict):
        return ProjectionData(
            Date=data["date"],
            Season=data["season"],
            Week=data["week"],
            PlayerID=data["player_id"],
            InjuryStatus=data["player"]["injury_status"],
            PointsHalfPPR=data["stats"].get("pts_half_ppr"),
            JSONData=json.dumps(data["stats"]),
            PointsNoTDs=data["pts_no_tds"],
            TDStats=data["td_stats"],
        )


def create_projections(conn: sqlite3.Connection, data: list[ProjectionData]):
    with conn:
        proj_query = """
            INSERT INTO Projections (Date, Season, Week, PlayerID, InjuryStatus, PointsHalfPPR, JSONData, PointsNoTDs, TDStats)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (Season, Week, PlayerID)
            DO UPDATE SET
                Date = excluded.Date,
                InjuryStatus = excluded.InjuryStatus,
                PointsHalfPPR = excluded.PointsHalfPPR,
                JSONData = excluded.JSONData,
                PointsNoTDs = excluded.PointsNoTDs,
                TDStats = excluded.TDStats
            """
        conn.executemany(proj_query, data)
