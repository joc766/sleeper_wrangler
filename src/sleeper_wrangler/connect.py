import sqlite3


def sleeper_connect():
    db_path = "/Users/jack/.local/share/sleeper/db.sqlite3"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
