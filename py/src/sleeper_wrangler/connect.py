import os
import sqlite3


def sleeper_connect():
    db_path = os.getenv("DB_PATH")
    if db_path is None:
        raise ValueError("set DB_PATH to the database path")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
