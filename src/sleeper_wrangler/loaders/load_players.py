import json
import sqlite3

from sleeper_wrangler.sleeper_api import get_players


# TODO: review and see why we have two functions here
def load_players():
    all_players = get_players()
    players_data = []
    for data in all_players.values():
        last_name = data["last_name"].replace("'", "''") if data["last_name"] else ""
        first_name = data["first_name"].replace("'", "''") if data["first_name"] else ""

        injury_status = (
            data["injury_status"] if data["injury_status"] is not None else "Healthy"
        )

        position = (
            "|".join(data["fantasy_positions"]) if data.get("fantasy_positions") else ""
        )
        players_data.append(
            (
                data["player_id"],
                data["team"],
                position,
                injury_status,
                last_name,
                first_name,
            )
        )


def load_players_data(conn: sqlite3.Connection, limit_to_existing=True):
    """
    Load NFL players data into the Player table.
    This should be run once or periodically to keep player data updated.

    Args:
        conn: Database connection
        limit_to_existing: If True, only load players that are already referenced in the database
    """
    try:
        players = get_players()

        # If limiting to existing players, get the list of player IDs already referenced
        existing_player_ids = set()
        if limit_to_existing:
            cursor = conn.cursor()
            # Get player IDs from draft picks
            cursor.execute(
                "SELECT DISTINCT PlayerID FROM DraftPick WHERE PlayerID IS NOT NULL"
            )
            draft_players = cursor.fetchall()
            existing_player_ids.update([row[0] for row in draft_players])

            # Get player IDs from matchup roster players (if that table exists and has data)
            cursor.execute(
                "SELECT DISTINCT PlayerID FROM MatchupRosterPlayer WHERE PlayerID IS NOT NULL"
            )
            roster_players = cursor.fetchall()
            existing_player_ids.update([row[0] for row in roster_players])

            print(
                f"Found {len(existing_player_ids)} existing player references in database"
            )

        player_qry = """
            INSERT OR REPLACE INTO Player (PlayerID, FirstName, LastName, FullName, Team, Position, Status, InjuryStatus, Age, Height, Weight, College, YearsExp, SearchRank, JSONData)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        players_data = []
        skipped_no_position = 0
        skipped_not_existing = 0

        for player_id, player_data in players.items():
            # Skip if limiting to existing and this player isn't referenced
            if limit_to_existing and player_id not in existing_player_ids:
                skipped_not_existing += 1
                continue

            # Skip players without position data (required field)
            position = player_data.get("position")
            if not position or position.strip() == "":
                skipped_no_position += 1
                continue

            first_name = player_data.get("first_name", "")
            last_name = player_data.get("last_name", "")
            full_name = f"{first_name} {last_name}".strip()

            players_data.append(
                (
                    player_id,
                    first_name,
                    last_name,
                    full_name,
                    player_data.get("team"),
                    position,  # Already validated above
                    player_data.get("status"),
                    player_data.get("injury_status"),
                    player_data.get("age"),
                    player_data.get("height"),
                    player_data.get("weight"),
                    player_data.get("college"),
                    player_data.get("years_exp"),
                    player_data.get("search_rank"),
                    json.dumps(player_data),
                )
            )

        cursor = conn.cursor()
        cursor.executemany(player_qry, players_data)
        conn.commit()

        print(f"Loaded {len(players_data)} players into database")
        if skipped_no_position > 0:
            print(f"Skipped {skipped_no_position} players due to missing position data")
        if skipped_not_existing > 0:
            print(
                f"Skipped {skipped_not_existing} players not referenced in existing data"
            )

    except:
        print("Error loading players data")
        raise
