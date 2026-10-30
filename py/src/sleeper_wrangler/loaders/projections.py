import json
import sqlite3

from sleeper_wrangler.connect import sleeper_connect
from sleeper_wrangler.db import (
    select_league_scoring_settings,
    select_leagueid_from_season,
)
from sleeper_wrangler.db.projection import ProjectionData, create_projections
from sleeper_wrangler.loaders.utils import (
    TD_STAT_KEYS,
    calc_league_specific_pts,
    calc_league_specific_pts_no_tds,
)
from sleeper_wrangler.sleeper_api import get_projections


def mock_projections() -> list:
    with open(
        "/Users/jack/workspace/github.com/joc766/sleeper_wrangler/refs/temp.json", "r"
    ) as f:
        data = json.load(f)
    return data


def load_projections(conn: sqlite3.Connection, season: str, week: int):
    projections = get_projections(season, week)
    league_id = select_leagueid_from_season(conn, season)
    scoring_settings = json.loads(select_league_scoring_settings(conn, league_id))
    proj_data = []
    for p in projections:
        p["stats"]["pts_half_ppr"] = calc_league_specific_pts(
            p["stats"], scoring_settings
        )
        p["pts_no_tds"] = calc_league_specific_pts_no_tds(p["stats"], scoring_settings)
        p["td_stats"] = json.dumps(
            {k: v for k, v in p["stats"].items() if k in TD_STAT_KEYS}
        )
        proj_data.append(ProjectionData.from_json(p))
    create_projections(conn, proj_data)


if __name__ == "__main__":
    conn = sleeper_connect()

    for season in ["2022", "2023", "2024", "2025", "2026"]:
        for week in range(1, 19):
            load_projections(conn, season, week)
