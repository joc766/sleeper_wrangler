import json
import sqlite3
from typing import NamedTuple

from rich.progress import track

from sleeper_wrangler.db.league import (
    select_league_scoring_settings,
    select_leagueid_from_season,
)
from sleeper_wrangler.loaders.projections import truncate
from sleeper_wrangler.sleeper_api import get_player_history


class PlayerHistory(NamedTuple):
    PlayerID: str
    Season: str
    Week: str
    PtsHalfPPR: float | None


# TODO: clean up with db functions
# TODO: only load as necessary for predictions?
def load_player_history(conn: sqlite3.Connection, season: str):
    with conn:
        league_id = select_leagueid_from_season(conn, season)
        scoring_settings = json.loads(select_league_scoring_settings(conn, league_id))
        players_query = "SELECT DISTINCT p.PlayerID FROM Player p JOIN MatchupRosterPlayer mrp on p.PlayerID = mrp.PlayerID"
        results = conn.execute(players_query).fetchall()
        if len(results) == 0:
            raise ValueError("Empty results for players query")
        player_ids = [row[0] for row in results]
        player_histories: list[PlayerHistory] = []
        for id in track(player_ids):
            data = get_player_history(id, season)
            for week, week_data in data.items():
                if week_data is not None:
                    # TODO: probably should refactor both this and projections calc logic into a single helper func
                    # Then we can do this as a list comprehension
                    league_pts = 0.0
                    for stat_key, amt in week_data["stats"].items():
                        if scoring_settings.get(stat_key) is not None:
                            league_pts += float(scoring_settings[stat_key]) * amt
                        player_histories.append(
                            PlayerHistory(
                                PlayerID=id,
                                Season=season,
                                Week=week,
                                PtsHalfPPR=truncate(league_pts, 2),
                            )
                        )

        history_query = """
            INSERT INTO PlayerHistory (PlayerID, Season, Week, PtsHalfPPR)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (PlayerID, Season, Week)
            DO UPDATE SET PtsHalfPPR = excluded.PtsHalfPPR
        """
        conn.executemany(history_query, player_histories)
