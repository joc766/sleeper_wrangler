import math
from pprint import pp


def truncate(number: float, decimals: int = 0) -> float:
    factor = 10**decimals
    return math.trunc(number * factor) / factor


def calc_league_specific_pts(stats: dict[str, float], settings: dict[str, float]):
    proj_points = 0.0
    for stat_key, proj_amt in stats.items():
        if stat_key in settings:
            proj_points += float(settings[stat_key]) * proj_amt
    return truncate(proj_points, 2)


TD_STAT_KEYS = {
    "st_td",
    "rec_td",
    "rush_td",
    "def_st_td",
    "def_td",
    "pass_td",
    "fum_rec_td",
}


def calc_league_specific_pts_no_tds(
    stats: dict[str, float], settings: dict[str, float]
):
    proj_points = 0.0
    for stat_key, proj_amt in stats.items():
        if stat_key in settings and stat_key not in TD_STAT_KEYS:
            proj_points += float(settings[stat_key]) * proj_amt
    return truncate(proj_points, 2)
