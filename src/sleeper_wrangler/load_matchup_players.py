
import json
from typing import NamedTuple

from sleeper_wrangler.get_data import sleeper_connect


class MatchupRosterPlayer(NamedTuple):
    MatchupRosterID: int
    PlayerID: str
    Position: str
    Starter: int
    Points: float
    ProjectedPoints: float | None
    JSONData: str | None

    

def load_matchup_players():
    mr_query = """
        SELECT MatchupRosterID, JSONData FROM MatchupRoster;
"""

    players_query = """
        SELECT PlayerID, Position FROM Player;
    """
    with sleeper_connect() as conn:
        cursor = conn.cursor()
        cursor.execute(mr_query)
        results = cursor.fetchall()
        cursor.execute(players_query)
        players_results = cursor.fetchall()

        if len(results) == 0 :
            raise ValueError("no matchup rosters returned by query.")

        if len(players_results) == 0 :
            raise ValueError("no matchup rosters returned by query.")

        players = {row[0]: row[1] for row in players_results}

        mr_players = []
        for row in results:
            mr_id = row[0]
            data = json.loads(row[1])
            for player_id, points in zip(data["starters"], data["starters_points"]):
                if player_id != "0":
                    position = players[player_id]
                    mr_player = MatchupRosterPlayer(
                        MatchupRosterID=mr_id,
                        PlayerID=player_id,
                        Position=position,
                        Starter=1,
                        Points=points,
                        ProjectedPoints=None,
                        JSONData=None
                    )
                    mr_players.append(mr_player)

        mr_players_query = """
            INSERT OR REPLACE INTO MatchupRosterPlayer (MatchupRosterID, PlayerID, Position, Starter, Points, ProjectedPoints, JSONData)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        cursor.executemany(mr_players_query, mr_players)
        conn.commit()



        
