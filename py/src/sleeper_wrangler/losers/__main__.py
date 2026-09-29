import json
import sys
import time
from datetime import date, timedelta

from sleeper_wrangler.connect import sleeper_connect
from sleeper_wrangler.db.league import select_leagueid_from_season
from sleeper_wrangler.espn_api import get_game_statuses
from sleeper_wrangler.loaders import (
    load_matchup_players,
    load_matchup_rosters,
    load_matchups,
    load_projections,
)
from sleeper_wrangler.losers import calc_loser_probs, calc_loser_probs_v2
from sleeper_wrangler.sleeper_api import get_nfl_state


def timeit(func):
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        return_val = func(*args, **kwargs)
        end_time = time.perf_counter()
        print(f"execution time: {end_time - start_time}", file=sys.stderr)
        return return_val

    return wrapper


nfl_state = get_nfl_state()
week = nfl_state.week
season = nfl_state.season
wk_start: date = nfl_state.season_start_date + timedelta(days=7 * (week - 1))
wk_end: date = nfl_state.season_start_date + timedelta(days=(7 * week) - 1)
conn = sleeper_connect()

league_id = select_leagueid_from_season(conn, season)

# timeit(load_matchups)(conn, league_id, week)
# timeit(load_matchup_rosters)(conn, league_id, week)
# timeit(load_matchup_players)(conn, league_id, week)
load_matchups(conn, league_id, week)
load_matchup_rosters(conn, league_id, week)
load_matchup_players(conn, league_id, week)

# load_projections should be a cron job, doesn't need to run every time we simulate
# load_projections(conn, league_id, week)

completion_by_team = get_game_statuses(wk_start, wk_end)
loser_probs = calc_loser_probs(season, week, completion_by_team)

# TODO: move insertion to LoserProjections to server?
data = json.dumps(loser_probs)
with conn:
    responseData = conn.execute(
        "INSERT INTO LoserProjections (ProjectionData, CreatedAt, GameStatus) VALUES (?, CURRENT_TIMESTAMP, ?) RETURNING CreatedAt",
        (data, json.dumps(completion_by_team)),
    ).fetchone()

json_data = json.dumps(
    {
        "projections": loser_probs,
        "created_at": responseData["CreatedAt"],
    }
)
print(json_data)
