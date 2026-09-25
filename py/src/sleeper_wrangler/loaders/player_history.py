from typing import NamedTuple

from sleeper_wrangler import sleeper_connect
from sleeper_wrangler.sleeper_api import get_player_history


class PlayerHistory(NamedTuple):
    PlayerID: str
    Season: str
    Week: str
    PtsHalfPPR: float | None


# TODO: clean up with db functions
# TODO: only load as necessary for predictions?
def load_player_history():
    players_query = "SELECT DISTINCT p.PlayerID FROM Player p JOIN MatchupRosterPlayer mrp on p.PlayerID = mrp.PlayerID"
    with sleeper_connect() as conn:
        cursor = conn.cursor()
        cursor.execute(players_query)
        results = cursor.fetchall()

        if len(results) == 0:
            raise ValueError("Empty results for players query")

        player_ids = [row[0] for row in results]
        player_histories: list[PlayerHistory] = []
        for szn in ["2025"]:
            for i, id in enumerate(player_ids):
                print(f"Loading history for {szn}: {i}/{len(player_ids)}")
                data = get_player_history(id, szn)
                for week, week_data in data.items():
                    if week_data is not None:
                        history = PlayerHistory(
                            PlayerID=id,
                            Season=szn,
                            Week=week,
                            PtsHalfPPR=week_data["stats"].get("pts_half_ppr"),
                        )
                        player_histories.append(history)

        history_query = """
            INSERT OR REPLACE INTO PlayerHistory (PlayerID, Season, Week, PtsHalfPPR)
            VALUES (?, ?, ?, ?)
        """
        cursor.executemany(history_query, player_histories)
