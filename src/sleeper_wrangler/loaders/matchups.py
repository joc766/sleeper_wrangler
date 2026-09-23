import json
import sqlite3

from sleeper_wrangler.sleeper_api import get_matchups


def load_matchups(conn: sqlite3.Connection, league_id: str):
    season: str = conn.execute(
        "SELECT Season FROM League WHERE LeagueID = ?", (league_id,)
    ).fetchone()["Season"]
    # MATCHUPS - Process with new schema
    matchups = get_matchups(league_id)

    # First, create Matchup records
    matchup_qry = """
        INSERT OR REPLACE INTO Matchup (LeagueID, Season, Week, MatchupCode, PlayoffRound, IsPlayoff, JSONData)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """

    # Group matchups by week and matchup_id to create unique Matchup records
    matchup_groups = {}
    for data in matchups:
        week = data["week"]
        matchup_id = data.get("matchup_id")
        key = (week, matchup_id)

        if key not in matchup_groups:
            # Determine if it's a playoff matchup (typically weeks 15+)
            is_playoff = 1 if week >= 15 else 0
            playoff_round = None
            if is_playoff:
                playoff_round = week - 14  # Simple playoff round calculation

            matchup_groups[key] = {
                "week": week,
                "matchup_id": matchup_id,
                "is_playoff": is_playoff,
                "playoff_round": playoff_round,
                "rosters": [],
            }

        matchup_groups[key]["rosters"].append(data)

    # Insert Matchup records
    matchup_data = []
    for key, matchup_info in matchup_groups.items():
        # Skip if MatchupCode is None (eliminated teams in playoffs)
        if matchup_info["matchup_id"] is None:
            print(
                f"Warning: Skipping matchup with None MatchupCode for week {matchup_info['week']}"
            )
            continue

        matchup_data.append(
            (
                league_id,
                season,
                matchup_info["week"],
                matchup_info["matchup_id"],
                matchup_info["playoff_round"],
                matchup_info["is_playoff"],
                json.dumps(matchup_info),
            )
        )
    conn.executemany(matchup_qry, matchup_data)

    # Now create MatchupRoster records
    matchup_roster_qry = """
        INSERT OR REPLACE INTO MatchupRoster (MatchupID, RosterCode, LeagueID, Season, Week, Points, ProjectedPoints, IsWinner, JSONData)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    matchup_roster_data = []
    for key, matchup_info in matchup_groups.items():
        # Get the MatchupID for this matchup
        try:
            matchup_id = conn.execute(
                """
                SELECT MatchupID FROM Matchup
                WHERE LeagueID = ? AND Week = ? AND MatchupCode = ?
            """,
                (league_id, matchup_info["week"], matchup_info["matchup_id"]),
            ).fetchone()["MatchupID"]
        except KeyError:
            print(f"error finding matchupID for {matchup_info['matchup_id']}")
            continue

        # Process each roster in the matchup
        rosters = matchup_info["rosters"]
        points_list = [r["points"] for r in rosters if r["points"] is not None]

        for roster in rosters:
            # Determine winner (highest points wins)
            is_winner = 0
            if roster["points"] is not None and points_list:
                max_points = max(points_list)
                if (
                    roster["points"] == max_points
                    and len([p for p in points_list if p == max_points]) == 1
                ):
                    is_winner = 1

            matchup_roster_data.append(
                (
                    matchup_id,
                    roster["roster_id"],
                    league_id,
                    season,
                    roster["week"],
                    roster["points"] or 0,
                    roster.get("projected_points"),
                    is_winner,
                    json.dumps(roster),
                )
            )

    conn.executemany(matchup_roster_qry, matchup_roster_data)
