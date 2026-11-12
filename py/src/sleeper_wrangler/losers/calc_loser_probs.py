import json
import math
import sqlite3
from collections import defaultdict
from enum import StrEnum, auto
from pprint import pp
from typing import NamedTuple

import numpy as np

from sleeper_wrangler import sleeper_connect
from sleeper_wrangler.db.league import (
    select_league_scoring_settings,
)
from sleeper_wrangler.db.utils import (
    select_historical_performances_enhanced,
    select_teams_and_starters_enhanced,
)
from sleeper_wrangler.espn_api import get_game_statuses
from sleeper_wrangler.loaders.utils import calc_league_specific_pts


class Player(NamedTuple):
    avatar: str | None
    team_current_pts: float
    player_id: str
    team_abbr: str
    position: str
    proj_pts: float
    injury_status: str | None
    curr_pts: float
    proj_pts_no_tds: float | None
    td_stats: dict[str, float]


class UserWeekData(NamedTuple):
    avatar: str | None
    current_points: float
    projected_points: float
    starters: list[Player]
    incomplete_lineup: bool


class SimulationMode(StrEnum):
    DEFAULT = auto()
    POISSON_TD = auto()


def round_values(pcts: dict[str, float]) -> dict[str, int]:
    rounded = {k: math.floor(v) for k, v in pcts.items()}
    remaining = 100 - sum(rounded.values())
    order = sorted(
        pcts.keys(),
        key=lambda k: pcts[k] - rounded[k],
        reverse=True,
    )
    for k in order[:remaining]:
        rounded[k] += 1
    return rounded


# TODO: Avatar should NOT be in a Player object, that makes no sense
def get_team_rosters_and_players_enhanced(
    conn: sqlite3.Connection, league_id: str, week: int, users: set[str] | None = None
) -> dict[str, list[Player]]:
    with conn:
        teams_and_starters = select_teams_and_starters_enhanced(conn, league_id, week)
        starters_by_username: dict[str, list[Player]] = defaultdict(list)
        for row in teams_and_starters:
            if users is None or row["UserName"] in users:
                starters_by_username[row["UserName"]].append(
                    Player(
                        avatar=row["Avatar"],
                        team_current_pts=row["TeamCurrentPoints"],
                        player_id=row["PlayerID"],
                        team_abbr=row["PlayerTeam"],
                        position=row["Position"],
                        proj_pts=row["ProjectedPoints"],
                        injury_status=row["InjuryStatus"],
                        curr_pts=row["CurrentPoints"],
                        proj_pts_no_tds=row["ProjectedPointsNoTDs"],
                        td_stats=json.loads(row["TDStats"])
                        if row["TDStats"] is not None
                        else {},
                    )
                )

        return starters_by_username


def simulate(
    error_pct: float,
    proj_pts_half_ppr: float,
    percent_complete: float,
) -> float:
    time = 1.0 - percent_complete
    # return proj_pts_half_ppr * time + proj_pts_half_ppr * np.sqrt(time) * error_pct
    return proj_pts_half_ppr * time + proj_pts_half_ppr * time * error_pct


# TODO: verify that injury status after a game is over will not mess up simulations
def simulate_player(
    player: Player,
    sampled_error: float,
    team_completion: float,
    scoring_settings: dict[str, float],
    mode: SimulationMode,
    sampled_td_stats: dict[str, float] | None = None,
) -> float:

    match mode:
        case SimulationMode.DEFAULT:
            projected = player.proj_pts
        case SimulationMode.POISSON_TD:
            projected = player.proj_pts_no_tds

    if player.injury_status and player.injury_status.strip().casefold() == "out":
        projected = 0.0

    if projected is None:
        projected = 0.0

    simulated_pts = player.curr_pts
    simulated_pts += simulate(
        sampled_error,
        projected,
        team_completion,
    )

    if mode == SimulationMode.POISSON_TD:
        if sampled_td_stats is None:
            raise ValueError("Must provide sampled_td_stats for mode POISSON_TD")
        simulated_pts += simulate_tds(sampled_td_stats, scoring_settings)

    return simulated_pts


def simulate_losses(
    league_id,
    starters_by_username: dict[str, list[Player]],
    completion_by_team: dict[str, float],
    sampled_errors_by_player: dict[str, np.typing.NDArray[np.float64]],
    mode: SimulationMode,
    sampled_tds_by_player: dict[str, dict[str, np.typing.NDArray[np.int64]]]
    | None = None,
    n_iterations: int = 10_000,
):
    if mode == SimulationMode.POISSON_TD and sampled_tds_by_player is None:
        raise ValueError(
            "Must provide sampled_tds_by_player for simulation mode POISSON_TD"
        )

    with sleeper_connect() as conn:
        scoring_settings = json.loads(select_league_scoring_settings(conn, league_id))

    losses = defaultdict(int)
    for i in range(n_iterations):
        scores: dict[str, float] = {
            username: sum(
                simulate_player(
                    p,
                    sampled_errors_by_player[p.player_id][i],
                    completion_by_team[p.team_abbr],
                    scoring_settings,
                    mode,
                    {k: v[i] for k, v in sampled_tds_by_player[p.player_id].items()}
                    if sampled_tds_by_player is not None
                    else None,
                )
                for p in starters
                if completion_by_team.get(p.team_abbr)
                is not None  # do not calculate for bye weeks
            )
            for username, starters in starters_by_username.items()
        }
        try:
            loser = min(scores, key=lambda k: scores[k])
        except:
            print(scores)
            raise
        losses[loser] += 1

    return {
        username: (losses / n_iterations) * 100
        for username, losses in sorted(losses.items(), key=lambda x: x[1])
    }


def simulate_tds(stats: dict[str, float], settings: dict[str, float]) -> float:
    return calc_league_specific_pts(stats, settings)


def create_errors_by_position(
    conn: sqlite3.Connection, player_ids: list[str], mode: SimulationMode
) -> dict[str, list[float]]:

    errors_by_position = defaultdict(list[float])

    with conn:
        performance_hist = select_historical_performances_enhanced(
            conn,
            player_ids,
        )

    for row in performance_hist:
        try:
            match mode:
                case SimulationMode.DEFAULT:
                    err_pct: float = row.error / row.projected_pts
                case SimulationMode.POISSON_TD:
                    err_pct: float = row.error_no_tds / row.projected_pts_no_tds

        except ZeroDivisionError:
            continue

        errors_by_position[row.position].append(err_pct)

    return errors_by_position


def sample_errors_by_player(
    rng: np.random.Generator,
    n_iterations: int,
    errors_by_position: dict[str, list[float]],
    players: list[Player],
) -> dict[str, np.typing.NDArray[np.float64]]:
    return {
        p.player_id: rng.choice(
            np.asarray(errors_by_position[p.position]), size=n_iterations
        )
        for p in players
    }


def sample_tds_by_player(
    rng: np.random.Generator,
    n_iterations: int,
    completion_by_team: dict[str, float],
    players: list[Player],
):
    return {
        p.player_id: {
            stat: rng.poisson(
                lam=(
                    0.0
                    if p.injury_status and p.injury_status.strip().casefold() == "out"
                    else proj_amt * (1 - completion_by_team[p.team_abbr])
                ),
                size=n_iterations,
            )
            for stat, proj_amt in p.td_stats.items()
        }
        for p in players
    }


def remaining_projection(player: Player):
    if player.injury_status and player.injury_status.strip().casefold() == "out":
        return 0.0

    return player.proj_pts


def create_user_week_data(
    starters_by_username: dict[str, list[Player]], completion_by_team: dict[str, float]
) -> dict[str, UserWeekData]:
    return {
        username: UserWeekData(
            starters[0].avatar,
            starters[0].team_current_pts,
            sum(
                player.curr_pts
                + remaining_projection(player)
                * (1.0 - completion_by_team[player.team_abbr])
                for player in starters
                if completion_by_team.get(player.team_abbr) is not None
            ),
            starters,
            any(p.proj_pts == 0 for p in starters)
        )
        for username, starters in starters_by_username.items()
    }


class HistoricalError(NamedTuple):
    err_pct: float
    err_pct_no_tds: float


# TODO: want to be able to simulate scenarios for testing: move sql queries outside
def calc_loser_data(
    conn: sqlite3.Connection,
    league_id: str,
    week: int,
    completion_by_team: dict[str, float],
    users: set[str] | None = None,
    mode: SimulationMode = SimulationMode.DEFAULT,
) -> tuple[dict[str, int], dict[str, UserWeekData]]:

    rng = np.random.default_rng()
    starters_by_username = get_team_rosters_and_players_enhanced(
        conn, league_id, week, users=users
    )

    players_by_id: dict[str, Player] = {
        p.player_id: p for players in starters_by_username.values() for p in players
    }

    errors_by_position = create_errors_by_position(
        conn, list(players_by_id.keys()), mode=mode
    )

    n_iterations = 10_000

    sampled_errors_by_player = sample_errors_by_player(
        rng, n_iterations, errors_by_position, list(players_by_id.values())
    )

    if mode == SimulationMode.POISSON_TD:
        sampled_tds_by_player = sample_tds_by_player(
            rng, n_iterations, completion_by_team, list(players_by_id.values())
        )
    else:
        sampled_tds_by_player = None

    percents: dict[str, float] = simulate_losses(
        league_id,
        starters_by_username,
        completion_by_team,
        sampled_errors_by_player,
        mode,
        sampled_tds_by_player,
        n_iterations,
    )

    user_week_data = create_user_week_data(starters_by_username, completion_by_team)

    return round_values(percents), user_week_data


def calc_loser_probs(
    conn: sqlite3.Connection,
    league_id: str,
    week: int,
    completion_by_team: dict[str, float],
    users: set[str] | None = None,
    mode: SimulationMode = SimulationMode.DEFAULT,
) -> dict[str, int]:
    probabilities, _ = calc_loser_data(
        conn, league_id, week, completion_by_team, users=users, mode=mode
    )
    return probabilities


if __name__ == "__main__":
    from datetime import datetime, timedelta

    from sleeper_wrangler import sleeper_connect

    conn = sleeper_connect()
    league_id = "1384538107809902592"
    wk_start = datetime.strptime("10-28-2026", "%m-%d-%Y").date()
    wk_end = wk_start + timedelta(days=5)
    game_statuses = get_game_statuses(wk_start, wk_end)
    # users = {"chinodechat", "sternowins"}
    conn = sleeper_connect()
    # pp(calc_loser_probs_poisson_tds(conn, league_id, 8, game_statuses, users=users))
    pp(
        calc_loser_probs(
            conn, league_id, 8, game_statuses, mode=SimulationMode.POISSON_TD
        )
    )
    # pp(calc_loser_probs("2026", 8, game_statuses, users=users))
    # pp(calc_loser_probs("2026", 8, game_statuses))
