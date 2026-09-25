import json
import sqlite3

from sleeper_wrangler.db import select_league_season
from sleeper_wrangler.sleeper_api import get_draft, get_draft_picks


# TODO: clean up with db function
def load_draft(conn: sqlite3.Connection, league_id: str):
    """
    Process draft data and insert into Draft and DraftPick tables.
    """
    draft = get_draft(league_id)
    draft_picks = get_draft_picks(draft["draft_id"])
    season = select_league_season(conn, league_id)

    # Insert draft record
    draft_qry = """
        INSERT OR REPLACE INTO Draft (DraftID, LeagueID, Season, Type, Status, StartTime, EndTime, Settings, JSONData)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    conn.execute(
        draft_qry,
        (
            draft["draft_id"],
            league_id,
            season,
            draft.get("type"),
            draft.get("status"),
            draft.get("start_time"),
            draft.get("end_time"),
            json.dumps(draft.get("settings", {})),
            json.dumps(draft),
        ),
    )

    # Insert draft picks
    if draft_picks:
        draft_pick_qry = """
            INSERT OR REPLACE INTO DraftPick (DraftID, LeagueID, Season, Round, Pick, RosterCode, PlayerID, PickTime, JSONData)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        picks_data = []
        for pick in draft_picks:
            picks_data.append(
                (
                    draft["draft_id"],
                    league_id,
                    season,
                    pick.get("round"),
                    pick.get("pick_no"),
                    pick.get("roster_id"),
                    pick.get("player_id"),
                    pick.get("picked_at"),
                    json.dumps(pick),
                )
            )
        conn.executemany(draft_pick_qry, picks_data)
