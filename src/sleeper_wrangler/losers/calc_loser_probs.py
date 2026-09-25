from collections import defaultdict
from dataclasses import dataclass
from typing import NamedTuple

import numpy as np

from sleeper_wrangler import sleeper_connect
from sleeper_wrangler.espn_api import get_game_statuses


class Player(NamedTuple):
    PlayerID: str
    TeamAbbr: str


@dataclass
class MatchupRosterData:
    Points: int
    Starters: list[Player]


@dataclass
class Game:
    projected: float
    actual: float


def simulate(
    rng: np.random.Generator,
    sigma: float,
    proj_pts_half_ppr: float,
    percent_complete: float,
):
    time = 1.0 - percent_complete
    mu_i = proj_pts_half_ppr * time
    sigma_i = sigma * np.sqrt(time)

    return rng.normal(loc=mu_i, scale=sigma_i)


# TODO: don't use cursor
def calc_loser_probs(season: str, week: int) -> dict[str, float]:
    rng = np.random.default_rng()
    with sleeper_connect() as conn:
        cursor = conn.cursor()
        teams_query = """
            SELECT u.UserName, r.TeamName, mr.MatchupRosterID, mr.Points, mrp.PlayerID, p.Team AS 'PlayerTeam'
            FROM User AS u
                JOIN Roster AS r on r.UserID = u.UserID
                JOIN League AS l on r.LeagueID = l.LeagueID
                JOIN MatchupRoster AS mr ON mr.RosterCode = r.RosterCode and mr.Season = r.Season and mr.LeagueID = r.LeagueID
                JOIN MatchupRosterPlayer AS mrp ON mrp.MatchupRosterID = mr.MatchupRosterID
                JOIN Player p ON mrp.PlayerID = p.PlayerID
            WHERE l.Season = ?
            AND mr.Week = ?;
        """
        cursor.execute(teams_query, (season, week))
        matchup_results = cursor.fetchall()
        team_rosters = {}
        all_players = []
        for row in matchup_results:
            username = row["UserName"]
            points = row["Points"]
            player_id = row["PlayerID"]
            team_abbr = row["PlayerTeam"]
            if team_rosters.get(username) is None:
                team_rosters[username] = MatchupRosterData(Points=points, Starters=[])
            team_rosters[username].Starters.append(Player(player_id, team_abbr))
            all_players.append(player_id)

        placeholders = ",".join(["?"] * len(all_players))
        proj_query = f"""
            SELECT proj.PlayerID, proj.Season, proj.Week, proj.PointsHalfPPR AS 'ProjectedPoints', ph.PtsHalfPPR AS 'ScoredPoints'
            FROM Projections proj
                LEFT JOIN PlayerHistory ph ON
                    proj.PlayerID = ph.PlayerID AND
                    proj.Season = ph.Season AND
                    proj.Week = ph.Week
            WHERE proj.PlayerID IN ({placeholders})
            AND (
                CAST(proj.Season AS INT) < {season}
                OR (
                    CAST(proj.Season AS INT) = {season} AND proj.Week <= {week}
                )
            );
        """
        cursor.execute(proj_query, all_players)
        proj_results = cursor.fetchall()

        errors_by_player: dict[str, list[float]] = defaultdict(list)

        # TODO: cleanup some of this formatting and put it in the calc_sigma function
        weekly_projections: dict[str, float] = {}
        for row in proj_results:
            row_player_id = row[0]
            row_season = row[1]
            row_week = row[2]
            row_proj = row[3]
            row_actual = row[4]
            if row_proj is not None:
                if row_season == season and row_week == week:
                    weekly_projections[row_player_id] = row_proj
                else:
                    # don't factor in errors of the week being predicted. All other weeks in proj_results are prior to season, week.
                    if row_actual is not None:
                        errors_by_player[row_player_id].append(row_actual - row_proj)

        player_sigmas = {
            player_id: np.std(errors) if len(errors) > 0 else 0
            for player_id, errors in errors_by_player.items()
        }
        completion_by_team = get_game_statuses()
        losses = defaultdict(int)
        n_iterations = 10_000
        for i in range(n_iterations):
            scores: dict[str, float] = {
                username: mr_data.Points
                + sum(
                    simulate(
                        rng,
                        player_sigmas.get(
                            player_id, 0.0
                        ),  # supply None when we have no sigmas (rookie first game/hasn't played since 2021)
                        weekly_projections[player_id],
                        completion_by_team[team_abbr],
                    )
                    for player_id, team_abbr in mr_data.Starters
                    if weekly_projections.get(player_id)
                    is not None  # don't calculate for players with no projection (injured), assumes a 0.
                )
                for username, mr_data in team_rosters.items()
            }
            loser = min(scores, key=lambda k: scores[k])
            losses[loser] += 1

        percents = {
            username: (losses / n_iterations) * 100
            for username, losses in sorted(losses.items(), key=lambda x: x[1])
        }
        return percents
