import json
import sqlite3

from sleeper_wrangler.db.league import select_league_season
from sleeper_wrangler.db.roster import CreateRosterParms, create_rosters
from sleeper_wrangler.sleeper_api import get_league_users, get_rosters


def parse_record(record_str):
    """
    Parse a record string like "WWLWWWWWWWLLWW" into wins, losses, ties.
    Returns (wins, losses, ties) as integers.
    """
    if not record_str:
        return 0, 0, 0

    wins = record_str.count("W")
    losses = record_str.count("L")
    ties = record_str.count("T")  # In case there are ties in the future

    return wins, losses, ties


def load_rosters(conn: sqlite3.Connection, league_id: str) -> None:
    rosters = get_rosters(league_id)
    season = select_league_season(conn, league_id)

    team_names = {
        user["user_id"]: user["metadata"]["team_name"]
        for user in get_league_users(league_id)
    }

    teams_data = []
    for r in rosters:
        metadata = r.get("metadata", {})
        settings = r.get("settings", {})
        user_id = r.get("owner_id", "removed_user")
        team_name = team_names.get(user_id, "Removed User's Team")
        record = metadata.get("record", "")
        wins, losses, ties = parse_record(record)
        teams_data.append(
            CreateRosterParms(
                UserID=user_id,
                RosterCode=r["roster_id"],
                LeagueID=league_id,
                Season=season,
                TeamName=team_name,
                Record=metadata.get("record", ""),
                Streak=metadata.get("streak"),
                Fpts=settings.get("fpts", 0.0),
                FptsAgainst=settings.get("fpts_against", 0.0),
                Wins=wins,
                Losses=losses,
                Ties=ties,
                JSONData=json.dumps(r),
            )
        )

    create_rosters(conn, teams_data)
