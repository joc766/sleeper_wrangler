import json
import sqlite3

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
    season = conn.execute(
        "SELECT Season FROM League WHERE LeagueID = ?", (league_id,)
    ).fetchone()["Season"]

    # TODO: rename Team to Roster and possibly make RosterID a foreign key in MatchupRoster
    # TODO: load players from this roster?
    teams_qry = """
        INSERT OR REPLACE INTO Team (UserID, RosterCode, LeagueID, Season, TeamName, Record, Streak, Fpts, FptsAgainst, Wins, Losses, Ties, JSONData)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    # query Sleeper API for team names
    team_names = {
        user["user_id"]: user["metadata"]["team_name"]
        for user in get_league_users(league_id)
    }

    teams_data = []
    for i, roster in enumerate(rosters):
        if roster is None:
            print(f"Warning: Roster at index {i} is None, skipping")
            continue

        owner_id = roster.get("owner_id")
        roster_id = roster.get("roster_id")

        if not owner_id or not roster_id:
            print(
                f"Warning: Roster at index {i} missing owner_id or roster_id, skipping"
            )
            continue

        team_name = team_names.get(owner_id, "unknown")
        metadata = roster.get("metadata", {}) or {}
        settings = roster.get("settings", {}) or {}
        record = metadata.get("record", "")
        wins, losses, ties = parse_record(record)

        teams_data.append(
            (
                owner_id,
                roster_id,
                league_id,
                season,
                team_name,
                record,
                metadata.get("streak"),
                settings.get("fpts", 0),
                settings.get("fpts_against", 0),
                wins,
                losses,
                ties,
                json.dumps(roster),
            )
        )

    if teams_data:
        conn.executemany(teams_qry, teams_data)
        print(f"Successfully processed {len(teams_data)} teams")
    else:
        print("Warning: No valid team data to process")
