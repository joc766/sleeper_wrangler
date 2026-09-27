import sqlite3


def select_player_positions(conn: sqlite3.Connection):
    players_query = """
        SELECT PlayerID, Position FROM Player;
    """
    with conn:
        return conn.execute(players_query).fetchall()
