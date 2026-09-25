import json
import sqlite3
from typing import NamedTuple

from sleeper_wrangler.sleeper_api import get_projections


class ProjectionData(NamedTuple):
    Date: str
    Season: str
    Week: int
    PlayerID: str
    InjuryStatus: str | None
    PointsHalfPPR: float | None

    @classmethod
    def from_json(cls, data: dict):
        return ProjectionData(
            Date=data["date"],
            Season=data["season"],
            Week=data["week"],
            PlayerID=data["player_id"],
            InjuryStatus=data["player"]["injury_status"],
            PointsHalfPPR=data["stats"].get("pts_half_ppr"),
        )


def mock_projections() -> list:
    with open(
        "/Users/jack/workspace/github.com/joc766/sleeper_wrangler/refs/temp.json", "r"
    ) as f:
        data = json.load(f)
    return data


# is it really necesary to add a db function for this? It's very brief
# TODO: clean up with db functions and use database to see which weeks/seasons we need projections for
# Exclude historical weeks if we already have the data as well as future weeks (sleeper endpoint for current week)
def load_projections(conn: sqlite3.Connection, season: str, week: int):
    projections = get_projections(season, week)
    with conn:
        proj_data = [
            ProjectionData.from_json(p) for p in projections if p["date"] is not None
        ]
        proj_query = """
            INSERT OR REPLACE INTO Projections (Date, Season, Week, PlayerID, InjuryStatus, PointsHalfPPR)
            VALUES (?, ?, ?, ?, ?, ?)
            """
        conn.executemany(proj_query, proj_data)
