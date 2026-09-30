import json
import math
import sqlite3
from typing import NamedTuple

from sleeper_wrangler.db import (
    select_league_settings,
    select_leagueid_from_season,
)
from sleeper_wrangler.sleeper_api import get_projections


class ProjectionData(NamedTuple):
    Date: str | None
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


def truncate(number: float, decimals: int = 0) -> float:
    factor = 10**decimals
    return math.trunc(number * factor) / factor


# TODO: account for the league's actual scoring when calculating projections
# TODO: clean up with db functions and use database to see which weeks/seasons we need projections for
# Exclude historical weeks if we already have the data as well as future weeks (sleeper endpoint for current week)
def load_projections(conn: sqlite3.Connection, season: str, week: int):
    projections = get_projections(season, week)
    league_id = select_leagueid_from_season(conn, season)
    league_settings = json.loads(select_league_settings(conn, league_id))
    with conn:
        proj_data = []
        for p in projections:
            proj_points = 0.0
            for stat_key, proj_amt in p["stats"].items():
                if stat_key in league_settings:
                    proj_points += float(league_settings[stat_key]) * proj_amt
            p["stats"]["pts_half_ppr"] = truncate(proj_points, 2)
            proj_data.append(ProjectionData.from_json(p))

        proj_query = """
            INSERT OR REPLACE INTO Projections (Date, Season, Week, PlayerID, InjuryStatus, PointsHalfPPR)
            VALUES (?, ?, ?, ?, ?, ?)
            """
        conn.executemany(proj_query, proj_data)
