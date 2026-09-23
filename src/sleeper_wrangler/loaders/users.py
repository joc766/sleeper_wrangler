import json
import sqlite3

from sleeper_wrangler.sleeper_api import get_league_users, get_user_data


def load_league_users(conn: sqlite3.Connection, league_id: str) -> None:
    league_users = get_league_users(league_id)
    team_data = {}
    user_qry = """
        INSERT OR REPLACE INTO User (UserID, UserName, DisplayName, Avatar, JSONData)
        VALUES (?, ?, ?, ?, ?)
    """
    users_data = []
    for data in league_users:
        team_name = data.get("metadata", {}).get("team_name", "")
        team_data[data["user_id"]] = team_name

        user_data = get_user_data(data["user_id"])
        users_data.append(
            (
                user_data["user_id"],
                user_data["username"],
                user_data["display_name"],
                user_data.get("avatar"),
                json.dumps(user_data),
            )
        )
    conn.executemany(user_qry, users_data)
