import json

from sleeper_wrangler.sleeper_api import get_league


def load_league(league_id, conn):
    """
    Processes and inserts all data related to a single league into the database.
    """
    league = get_league(league_id)
    league_qry = """
        INSERT OR REPLACE INTO League (LeagueID, Season, Name, Previous_League_ID, DraftID, Status, Settings, ScoringSettings, RosterPositions, JSONData)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    league_data = (
        league["league_id"],
        league["season"],
        league["name"],
        league.get("previous_league_id"),
        league.get("draft_id"),
        league.get("status", "complete"),
        json.dumps(league.get("settings", {})),
        json.dumps(league.get("scoring_settings", {})),
        json.dumps(league.get("roster_positions", [])),
        json.dumps(league),
    )
    conn.execute(league_qry, league_data)

    conn.commit()
    return league["previous_league_id"]
