from contextlib import closing

from sleeper_wrangler import sleeper_connect
from sleeper_wrangler.loaders import (
    calculate_season_stats,
    calculate_weekly_stats,
    load_draft,
    load_league,
)


def main():
    # List of league IDs to process
    # league_ids = ['1120774194318479360', '868563615295410176', '990267272524541952'] # new to old, here for reference
    # latest_league_id = "1219656680917176320"
    latest_league_id = "1384538107809902592"

    # Connect to the database and process each league
    with closing(sleeper_connect()) as conn:
        try:
            # Process all leagues first
            curr_league = latest_league_id
            while curr_league is not None:
                try:
                    print(f"Processing league: {curr_league}")
                    # TODO: should we not return next league and just query for it? ensures success
                    next_league = load_league(curr_league, conn)

                    load_draft(conn, curr_league)

                    # Calculate and insert weekly stats
                    calculate_weekly_stats(conn, curr_league)

                    # Calculate and insert season stats
                    calculate_season_stats(conn, curr_league)
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
