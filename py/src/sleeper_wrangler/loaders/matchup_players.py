import json
import sqlite3
from typing import NamedTuple

from sleeper_wrangler.db.matchup import refresh_mr_players, select_matchup_rosters
from sleeper_wrangler.db.player import select_player_positions


class MatchupRosterPlayer(NamedTuple):
    MatchupRosterID: int
    PlayerID: str
    Position: str
    Starter: int
    Points: float
    ProjectedPoints: float | None
    JSONData: str | None


# TODO: revisit INSERT OR REPLACE logic. Doesn't currently break since the matchup replace changes the primary key.
# However, the goal is for matchup IDs to remain constant and therefore we would be creating dupes with this logic
def load_matchup_players(conn: sqlite3.Connection, league_id: str, week: int):
    # TODO: load all players, not just starters
    matchup_rosters = select_matchup_rosters(conn, league_id, week)
    player_positions = select_player_positions(conn)

    if len(matchup_rosters) == 0:
        raise ValueError("no matchup rosters returned by query.")

    if len(player_positions) == 0:
        raise ValueError("no matchup rosters returned by query.")

    positions_by_playerid = {row[0]: row[1] for row in player_positions}

    mr_players = []
    for mr in matchup_rosters:
        mr_id = mr["MatchupRosterID"]
        data = json.loads(mr["JSONData"])
        for player_id, points in zip(data["starters"], data["starters_points"]):
            if player_id != "0":
                position = positions_by_playerid[player_id]
                mr_player = MatchupRosterPlayer(
                    MatchupRosterID=mr_id,
                    PlayerID=player_id,
                    Position=position,
                    Starter=1,
                    Points=points,
                    ProjectedPoints=None,
                    JSONData=None,
                )
                mr_players.append(mr_player)

    refresh_mr_players(conn, mr_players)
