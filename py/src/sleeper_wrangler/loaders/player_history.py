import json
import sqlite3

from rich.progress import track

from sleeper_wrangler.connect import sleeper_connect
from sleeper_wrangler.db.league import (
    select_league_scoring_settings,
    select_leagueid_from_season,
)
from sleeper_wrangler.db.player import select_distinct_players
from sleeper_wrangler.db.player_history import PlayerHistory, upsert_player_history
from sleeper_wrangler.loaders.utils import (
    TD_STAT_KEYS,
    calc_league_specific_pts,
    calc_league_specific_pts_no_tds,
)
from sleeper_wrangler.sleeper_api import get_player_history


# TODO: only load as necessary for predictions?
def load_player_history(conn: sqlite3.Connection, season: str):
    league_id = select_leagueid_from_season(conn, season)
    scoring_settings = json.loads(select_league_scoring_settings(conn, league_id))
    player_ids = select_distinct_players(conn)
    if len(player_ids) == 0:
        raise ValueError("Empty results for players query")
    player_histories: list[PlayerHistory] = []
    for id in track(player_ids):
        data = get_player_history(id, season)
        player_histories.extend(
            PlayerHistory(
                PlayerID=id,
                Season=season,
                Week=week,
                PtsHalfPPR=calc_league_specific_pts(
                    week_data["stats"], scoring_settings
                ),
                JSONData=json.dumps(week_data["stats"]),
                PointsNoTDs=calc_league_specific_pts_no_tds(
                    week_data["stats"], scoring_settings
                ),
                TDStats=json.dumps(
                    {k: v for k, v in week_data["stats"].items() if k in TD_STAT_KEYS}
                ),
            )
            for week, week_data in data.items()
            if week_data is not None
        )

    upsert_player_history(conn, player_histories)


if __name__ == "__main__":
    conn = sleeper_connect()
    for season in ["2024", "2025", "2026"]:
        load_player_history(conn, season)
