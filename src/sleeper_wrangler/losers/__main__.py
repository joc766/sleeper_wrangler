import time

from sleeper_wrangler.connect import sleeper_connect
from sleeper_wrangler.db.league import select_leagueid_from_season
from sleeper_wrangler.loaders import (
    load_matchup_players,
    load_matchup_rosters,
    load_matchups,
)
from sleeper_wrangler.losers import calc_loser_probs
from sleeper_wrangler.sleeper_api import get_nfl_state


def timeit(func):
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        return_val = func(*args, **kwargs)
        end_time = time.perf_counter()
        print(f"execution time: {end_time - start_time}")
        return return_val

    return wrapper


nfl_state = get_nfl_state()
week = nfl_state.week
season = nfl_state.season
conn = sleeper_connect()

league_id = select_leagueid_from_season(conn, season)

timeit(load_matchups)(conn, league_id, week)
timeit(load_matchup_rosters)(conn, league_id, week)
timeit(load_matchup_players)(conn, league_id, week)

loser_probs = timeit(calc_loser_probs)(season, week)

print(loser_probs)
