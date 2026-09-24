import json
import sqlite3
from collections import defaultdict
from typing import NamedTuple

from sleeper_wrangler.db.league import select_league_season
from sleeper_wrangler.db.matchup import (
    InsertMatchupParms,
    InsertMatchupRosterParms,
    insert_matchup_rosters,
    insert_matchups,
    select_matchups,
)
from sleeper_wrangler.db.roster import select_rosters
from sleeper_wrangler.sleeper_api import get_matchups


class MatchupKey(NamedTuple):
    week: int
    matchup_id: int


def load_matchups(conn: sqlite3.Connection, league_id: str):
    season: str = select_league_season(conn, league_id)
    matchups: list[dict] = get_matchups(league_id)

    # Group matchups by week and matchup_id to create unique Matchup records
    matchup_rosters_by_key = defaultdict(list)
    key_func = lambda x: MatchupKey(x["week"], x["matchup_id"])
    for matchup_week in matchups:
        for m in matchup_week:
            matchup_rosters_by_key[key_func(m)].append(m)

    matchup_rows: list[InsertMatchupParms] = [
        InsertMatchupParms(
            LeagueID=league_id,
            Season=season,
            Week=week,
            MatchupCode=matchup_id,
            IsPlayoff=1 if week >= 15 else 0,
            PlayoffRound=week - 14,
            JSONData=json.dumps(matchup_rosters),
        )
        for (week, matchup_id), matchup_rosters in matchup_rosters_by_key.items()
    ]
    insert_matchups(conn, matchup_rows)


def load_matchup_rosters(conn: sqlite3.Connection, league_id: str):
    rosters_by_code = {
        r.RosterCode: r.RosterID for r in select_rosters(conn, league_id)
    }
    matchup_roster_data = []

    for m in select_matchups(conn, league_id):
        rosters: list = json.loads(m.JSONData)
        matchup_roster_data.extend(
            InsertMatchupRosterParms(
                MatchupID=m.MatchupID,
                RosterCode=r["roster_id"],
                RosterID=rosters_by_code[r["roster_id"]],
                LeagueID=league_id,
                Season=m.Season,
                Week=m.Week,
                Points=r["points"],
                IsWinner=int(r["points"] > rosters[i ^ 1]["points"]),
                JSONData=json.dumps(r),
            )
            for i, r in enumerate(rosters)
        )
    insert_matchup_rosters(conn, matchup_roster_data)
