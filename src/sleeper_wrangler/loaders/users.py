import json
import sqlite3

from sleeper_wrangler.db.user import CreateUsersParms, create_users
from sleeper_wrangler.sleeper_api import get_league_users


def load_league_users(conn: sqlite3.Connection, league_id: str) -> None:
    users_data = [
        CreateUsersParms(
            UserID=user_data["user_id"],
            UserName=user_data["display_name"].lower(),
            DisplayName=user_data["display_name"],
            JSONData=json.dumps(user_data),
            Avatar=user_data.get("avatar"),
        )
        for user_data in get_league_users(league_id)
    ]
    create_users(conn, users_data)
