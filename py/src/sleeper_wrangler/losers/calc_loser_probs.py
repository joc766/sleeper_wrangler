import math
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from typing import NamedTuple

import numpy as np

from sleeper_wrangler import sleeper_connect
from sleeper_wrangler.db.utils import (
    select_historical_performances,
    select_teams_and_starters,
)


class Player(NamedTuple):
    avatar: str | None
    team_current_pts: float
    player_id: str
    team_abbr: str
    position: str
    proj_pts: float
    injury_status: str | None
    curr_pts: float


class UserWeekData(NamedTuple):
    avatar: str | None
    current_points: float
    projected_points: float


@dataclass
class MatchupRosterData:
    Points: int
    Starters: list[Player]


@dataclass
class Game:
    projected: float
    actual: float


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


def get_team_rosters_and_players(
    conn: sqlite3.Connection, season: str, week: int
) -> dict[str, list[Player]]:
    with conn:
        teams_and_starters = select_teams_and_starters(conn, season, week)
        starters_by_username: dict[str, list[Player]] = defaultdict(list)
        for row in teams_and_starters:
            starters_by_username[row["UserName"]].append(
                Player(
                    row["Avatar"],
                    row["TeamCurrentPoints"],
                    row["PlayerID"],
                    row["PlayerTeam"],
                    row["Position"],
                    row["ProjectedPoints"],
                    row["InjuryStatus"],
                    row["CurrentPoints"],
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


def remaining_projection(player: Player) -> float:
    if player.injury_status and player.injury_status.strip().casefold() == "out":
        return 0.0
    return player.proj_pts


def calc_loser_data(
    season: str, week: int, completion_by_team: dict[str, float]
) -> tuple[dict[str, int], dict[str, UserWeekData]]:
    rng = np.random.default_rng()
    with sleeper_connect() as conn:
        starters_by_username = get_team_rosters_and_players(conn, season, week)
        performance_hist = select_historical_performances(
            conn,
            [p.player_id for players in starters_by_username.values() for p in players],
        )

    players_by_id: dict[str, Player] = {
        p.player_id: p for players in starters_by_username.values() for p in players
    }
    all_players: list[Player] = list(players_by_id.values())
    errors_by_position = defaultdict(list)
    for row in performance_hist:
        try:
            err_as_pct = row["error"] / row["projected"]
        except ZeroDivisionError:
            continue
        errors_by_position[row["Position"]].append(err_as_pct)

    losses = defaultdict(int)
    n_iterations = 10_000

    sampled_errors_by_player = {
        p.player_id: rng.choice(
            np.asarray(errors_by_position[p.position]), size=n_iterations
        )
        for p in all_players
    }

    for i in range(n_iterations):
        scores: dict[str, float] = {
            username: sum(
                simulate(
                    sampled_errors_by_player[p.player_id][i],
                    remaining_projection(p),
                    completion_by_team[p.team_abbr],
                )
                + p.curr_pts
                for p in starters
                if completion_by_team.get(p.team_abbr)
                is not None  # do not calculate for bye weeks
            )
            for username, starters in starters_by_username.items()
        }
        loser = min(scores, key=lambda k: scores[k])
        losses[loser] += 1

    percents = {
        username: (losses / n_iterations) * 100
        for username, losses in sorted(losses.items(), key=lambda x: x[1])
    }
    user_week_data = {
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
        )
        for username, starters in starters_by_username.items()
    }
    return round_values(percents), user_week_data


def calc_loser_probs(
    season: str, week: int, completion_by_team: dict[str, float]
) -> dict[str, int]:
    probabilities, _ = calc_loser_data(season, week, completion_by_team)
    return probabilities
