from collections import defaultdict
from dataclasses import dataclass

import numpy as np

from sleeper_wrangler.get_data import sleeper_connect
from sleeper_wrangler.load_projections import calc_sigma, simulate


@dataclass
class MatchupRosterData:
    Points: int
    Starters: list[str]


def calc_loser_prob(season: str, week: int):
    rng = np.random.default_rng()
    with sleeper_connect() as conn:
        cursor = conn.cursor()
        teams_query = """
            SELECT u.UserName, t.TeamName, mr.MatchupRosterID, mr.Points, mrp.PlayerID
            FROM User AS u
                JOIN Team AS t on t.UserID = u.UserID
                JOIN League AS l on t.LeagueID = l.LeagueID
                JOIN MatchupRoster AS mr ON mr.RosterCode = t.RosterCode and mr.Season = t.Season and mr.LeagueID = t.LeagueID
                JOIN MatchupRosterPlayer AS mrp on mrp.MatchupRosterID = mr.MatchupRosterID
            WHERE l.Season = ?
            AND mr.Week = ?;
        """
        cursor.execute(teams_query, (season, week))
        matchup_results = cursor.fetchall()
        team_rosters = {}
        all_players = []
        for row in matchup_results:
            username = row[0]
            points = row[3]
            player_id = row[-1]
            if team_rosters.get(username) is None:
                team_rosters[username] = MatchupRosterData(Points=points, Starters=[])
            team_rosters[username].Starters.append(player_id)
            all_players.append(player_id)

        placeholders = ",".join(["?"] * len(all_players))
        proj_query = f"""
            SELECT PlayerID, Season, Week, PointsHalfPPR FROM Projections
            WHERE PlayerID IN ({placeholders})
        """
        cursor.execute(proj_query, all_players)
        proj_results = cursor.fetchall()

        all_projections = defaultdict(list)
        weekly_projections = defaultdict(int)
        for row in proj_results:
            row_player_id = row[0]
            row_season = row[1]
            row_week = row[2]
            row_pts_half_ppr = row[3]
            if row_pts_half_ppr is not None:
                if row_season == season and row_week == week:
                    weekly_projections[row_player_id] = row_pts_half_ppr
                all_projections[row_player_id].append(row_pts_half_ppr)

        player_sigmas = {
            player_id: calc_sigma(projections)
            for player_id, projections in all_projections.items()
        }

        losses = defaultdict(int)
        for i in range(10_000):
            scores: dict[str, float] = {
                # TODO: need percent complete from espn api
                username: mr_data.Points + sum(
                    simulate(rng, player_sigmas[player_id], weekly_projections[player_id], 0.0) 
                    for player_id in mr_data.Starters
                )
                for username, mr_data in team_rosters.items()
            }
            loser = min(scores, key=lambda k: scores[k])
            losses[loser] += 1

        print(losses)
