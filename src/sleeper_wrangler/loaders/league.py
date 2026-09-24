import json
import sqlite3

from sleeper_wrangler.db.league import InsertLeagueParms, create_league
from sleeper_wrangler.sleeper_api import get_league


def load_league(conn: sqlite3.Connection, league_id: str):
    """
    Processes and inserts all data related to a single league into the database.
    """
    league = get_league(league_id)
    league_data = InsertLeagueParms(
        LeagueID=league["league_id"],
        Season=league["season"],
        Name=league["name"],
        Previous_League_ID=league.get("previous_league_id"),
        DraftID=league.get("draft_id"),
        Status=league.get("status", "complete"),
        Settings=json.dumps(league.get("settings", {})),
        ScoringSettings=json.dumps(league.get("scoring_settings", {})),
        RosterPositions=json.dumps(league.get("roster_positions", [])),
        JSONData=json.dumps(league),
    )
    create_league(conn, league_data)
    return league_data.Previous_League_ID
