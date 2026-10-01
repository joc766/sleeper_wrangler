import json
import math
import time
from contextlib import closing

from sleeper_wrangler import sleeper_connect
from sleeper_wrangler.db.league import select_league_settings
from sleeper_wrangler.loaders import (
    # calculate_season_stats,
    # calculate_weekly_stats,
    load_draft,
    load_league,
    load_rosters,
)
from sleeper_wrangler.loaders.matchup_players import load_matchup_players
from sleeper_wrangler.loaders.matchups import load_matchup_rosters, load_matchups
from sleeper_wrangler.loaders.players import load_players_data
from sleeper_wrangler.loaders.users import load_league_users


def main():
    # List of league IDs to process
    # league_ids = ['1120774194318479360', '868563615295410176', '990267272524541952'] # new to old, here for reference
    # latest_league_id = "1219656680917176320"
    latest_league_id = "1384538107809902592"

    # Connect to the database and process each league
    with closing(sleeper_connect()) as conn:
        try:
            load_players_data(conn, limit_to_existing=False)
            # Process all leagues first
            curr_league = latest_league_id
            while curr_league is not None:
                try:
                    print(f"Processing league: {curr_league}")
                    # TODO: should we not return next league and just query for it? ensures success
                    next_league = load_league(conn, curr_league)

                    load_draft(conn, curr_league)

                    load_league_users(conn, curr_league)

                    load_rosters(conn, curr_league)

                    league_settings = json.loads(
                        select_league_settings(conn, curr_league)
                    )
                    start_week: int = league_settings["start_week"]
                    playoff_start_week: int = league_settings["playoff_week_start"]
                    playoff_teams: int = league_settings["playoff_teams"]
                    playoff_weeks = math.ceil(math.log2(playoff_teams))
                    end_week = playoff_start_week + playoff_weeks - 1

                    for i in range(start_week, end_week + 1):
                        print(f"Loading week: {i}")
                        load_matchups(conn, curr_league, i)
                        load_matchup_rosters(conn, curr_league, i)
                        load_matchup_players(conn, curr_league, i)
                        time.sleep(0.5)

                    # Calculate and insert weekly stats
                    #                     calculate_weekly_stats(conn, curr_league)
                    #
                    #                     # Calculate and insert season stats
                    #                     calculate_season_stats(conn, curr_league)
                    print(f"Successfully processed league: {curr_league}")
                    curr_league = next_league
                except Exception as e:
                    print(f"Error processing league {curr_league}: {e}")
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
