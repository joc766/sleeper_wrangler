import json
import math
import time
from contextlib import closing

from sleeper_wrangler import sleeper_connect
from sleeper_wrangler.db.league import (
    InsertLeagueParms,
    create_league,
    create_master_league,
    select_league,
    select_league_settings,
)
from sleeper_wrangler.loaders import (
    # calculate_season_stats,
    # calculate_weekly_stats,
    load_draft,
    # load_league,
    load_rosters,
)
from sleeper_wrangler.loaders.matchup_players import load_matchup_players
from sleeper_wrangler.loaders.matchups import load_matchup_rosters, load_matchups
from sleeper_wrangler.loaders.players import load_players_data
from sleeper_wrangler.loaders.users import load_league_users
from sleeper_wrangler.sleeper_api import (
    get_all_leagues,
    get_nfl_state,
    get_user_league_id,
)


def main():
    # List of league IDs to process
    # league_ids = ['1120774194318479360', '868563615295410176', '990267272524541952'] # new to old, here for reference
    # latest_league_id = "1219656680917176320"
    primary_user_id = "871400057960878080"  # jack's userid
    nfl_state = get_nfl_state()
    season = nfl_state.season
    latest_league_id = get_user_league_id(primary_user_id, season)
    leagues = get_all_leagues(latest_league_id)
    initial_league = leagues[0]

    # Connect to the database and process each league
    with closing(sleeper_connect()) as conn:
        try:
            existing_league = select_league(conn, initial_league["league_id"])
            print(existing_league)
            master_league_id = (
                create_master_league(conn)
                if existing_league is None or existing_league["MasterLeagueID"] is None
                else existing_league["MasterLeagueID"]
            )

            load_players_data(conn, limit_to_existing=False)
            # Process all leagues first
            curr_league = latest_league_id
            for curr_league in leagues:
                curr_league_id = curr_league["league_id"]
                try:
                    print(f"Processing league: {curr_league_id}")
                    league_data = InsertLeagueParms(
                        LeagueID=curr_league["league_id"],
                        Season=curr_league["season"],
                        Name=curr_league["name"],
                        Previous_League_ID=curr_league.get("previous_league_id"),
                        DraftID=curr_league.get("draft_id"),
                        Status=curr_league.get("status", "complete"),
                        Settings=json.dumps(curr_league.get("settings", {})),
                        ScoringSettings=json.dumps(
                            curr_league.get("scoring_settings", {})
                        ),
                        RosterPositions=json.dumps(
                            curr_league.get("roster_positions", [])
                        ),
                        JSONData=json.dumps(curr_league),
                        MasterLeagueID=master_league_id,
                    )
                    create_league(conn, league_data)
                    # _ = load_league(conn, curr_league, master_league_id)

                    load_draft(conn, curr_league_id)

                    load_league_users(conn, curr_league_id)

                    load_rosters(conn, curr_league_id)

                    league_settings = json.loads(
                        select_league_settings(conn, curr_league_id)
                    )
                    start_week: int = league_settings["start_week"]
                    playoff_start_week: int = league_settings["playoff_week_start"]
                    playoff_teams: int = league_settings["playoff_teams"]
                    playoff_weeks = math.ceil(math.log2(playoff_teams))
                    end_week = playoff_start_week + playoff_weeks - 1

                    for i in range(start_week, end_week + 1):
                        print(f"Loading week: {i}")
                        load_matchups(conn, curr_league_id, i)
                        load_matchup_rosters(conn, curr_league_id, i)
                        load_matchup_players(conn, curr_league_id, i)
                        time.sleep(0.5)

                    # Calculate and insert weekly stats
                    #                     calculate_weekly_stats(conn, curr_league)
                    #
                    #                     # Calculate and insert season stats
                    #                     calculate_season_stats(conn, curr_league)
                    print(f"Successfully processed league: {curr_league_id}")
                except Exception as e:
                    print(f"Error processing league {curr_league_id}: {e}")
                    raise

            # Load players data at the end, limiting to players already referenced in the database
            # print("Loading players data (limited to existing references)...")
            # load_players_data(conn, limit_to_existing=True)

        except Exception as e:
            print(f"Database error: {e}")
            raise
        finally:
            print("Processing complete.")


if __name__ == "__main__":
    main()
