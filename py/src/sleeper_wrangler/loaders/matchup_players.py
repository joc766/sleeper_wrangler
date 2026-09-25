import json
import sqlite3
from typing import NamedTuple


class MatchupRosterPlayer(NamedTuple):
    MatchupRosterID: int
    PlayerID: str
    Position: str
    Starter: int
    Points: float
    ProjectedPoints: float | None
    JSONData: str | None


def load_matchup_players(conn: sqlite3.Connection, league_id: str, week: int):
    mr_query = """
        SELECT MatchupRosterID, JSONData FROM MatchupRoster WHERE LeagueID = ? AND Week = ?;
    """

    players_query = """
        SELECT PlayerID, Position FROM Player;
    """
    # TODO: load all players, not just starters
    with conn:
        results = conn.execute(mr_query, (league_id, week)).fetchall()
        players_results = conn.execute(players_query).fetchall()

        if len(results) == 0:
            raise ValueError("no matchup rosters returned by query.")

        if len(players_results) == 0:
            raise ValueError("no matchup rosters returned by query.")

        positions_by_playerid = {row[0]: row[1] for row in players_results}

        mr_players = []
        for row in results:
            mr_id = row[0]
            data = json.loads(row[1])
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

        mr_players_query = """
            INSERT OR REPLACE INTO MatchupRosterPlayer (MatchupRosterID, PlayerID, Position, Starter, Points, ProjectedPoints, JSONData)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        conn.executemany(mr_players_query, mr_players)
