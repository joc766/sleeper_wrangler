import json
import sqlite3
from typing import NamedTuple

from sleeper_wrangler.get_data import sleeper_connect


class ProjectionData(NamedTuple):
    Date: str
    Season: str
    Week: int
    PlayerID: str
    InjuryStatus: str | None
    PointsHalfPPR: float | None

    @classmethod
    def from_json(cls, data: dict):
        return ProjectionData(
            Date=data["date"],
            Season=data["season"],
            Week=data["week"],
            PlayerID=data["player_id"],
            InjuryStatus=data["player"]["injury_status"],
            PointsHalfPPR=data["stats"].get("pts_half_ppr"),
        )


def mock_projections() -> list:
    with open("/Users/jack/workspace/github.com/joc766/sleeper_wrangler/refs/temp.json", "r") as f:
        data = json.load(f)
    return data


def process_projections(data: list[dict]):
    if type(data) != list:
        raise ValueError(f"Received non-list object: {data}")

    conn = sleeper_connect()
    cursor = conn.cursor()

    try:
        proj_data = [ProjectionData.from_json(row) for row in data if row["date"] is not None]
        proj_query = """
            INSERT OR REPLACE INTO Projections (Date, Season, Week, PlayerID, InjuryStatus, PointsHalfPPR) 
            VALUES (?, ?, ?, ?, ?, ?)
            """
        cursor.executemany(proj_query, proj_data)
        conn.commit()


    except sqlite3.IntegrityError as e:
        print(f"Integrity error occurred: {e}")
        conn.rollback()

    except sqlite3.ProgrammingError as e:
        print(f"Programming error occurred: {e}")
        conn.rollback()

    except sqlite3.Error as e:
        print(f"General database error: {e}")
        conn.rollback()

    finally:
        conn.close()


if __name__ == "__main__":
    data = mock_projections()
    process_projections(data)
