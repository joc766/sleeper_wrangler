import sqlite3
import json
from sleeper_api import get_league, get_league_users, get_matchups, get_rosters, get_user_data

def process_league(league_id, conn):
    """
    Processes and inserts all data related to a single league into the database.
    """
    cursor = conn.cursor()

    # LEAGUE
    league = get_league(league_id)
    league_qry = '''
        INSERT INTO League (LeagueID, Season, JSONData, Previous_League_ID, Name, DraftID)
        VALUES (?, ?, ?, ?, ?, ?)
    '''
    league_data = (
        league["league_id"],
        league["season"],
        json.dumps(league),
        league["previous_league_id"],
        league["name"],
        league["draft_id"],
    )
    cursor.execute(league_qry, league_data)

    # USERS
    league_users = get_league_users(league_id)
    team_data = {}
    user_qry = '''
        INSERT OR IGNORE INTO [User] (UserID, UserName, DisplayName, JSONData)
        VALUES (?, ?, ?, ?)
    '''
    users_data = []
    for data in league_users:
        team_name = data.get("metadata", {}).get("team_name", "")
        team_data[data["user_id"]] = team_name

        user_data = get_user_data(data["user_id"])
        users_data.append((
            user_data["user_id"],
            user_data["username"],
            user_data["display_name"],
            json.dumps(user_data),
        ))
    cursor.executemany(user_qry, users_data)

    # TEAMS
    rosters = get_rosters(league_id)
    teams_qry = '''
        INSERT INTO Team (UserID, RosterCode, LeagueID, TeamName, Record, Streak, Fpts, FptsAgainst)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    '''
    teams_data = []
    for data in rosters:
        team_name = team_data.get(data.get('owner_id'), 'unknown')
        teams_data.append((
            data.get("owner_id"),
            data["roster_id"],
            league_id,
            team_name,
            data.get("metadata", {}).get("record"),
            data.get("metadata", {}).get("streak"),
            data.get("settings", {}).get("fpts"),
            data.get("settings", {}).get("fpts_against"),
        ))
    cursor.executemany(teams_qry, teams_data)

    # MATCHUPS
    matchups = get_matchups(league_id)
    matchup_roster_qry = '''
        INSERT INTO MatchupRoster (LeagueID, MatchupCode, RosterCode, Week, Points)
        VALUES (?, ?, ?, ?, ?)
    '''
    matchups_data = []
    for data in matchups:
        matchups_data.append((
            league_id,
            data.get("matchup_id"),
            data["roster_id"],
            data["week"],
            data["points"],
        ))
    cursor.executemany(matchup_roster_qry, matchups_data)

    conn.commit()
    return league["previous_league_id"]


def main():
    # List of league IDs to process
    league_ids = ['1120774194318479360', '868563615295410176', '990267272524541952'] # new to old, here for reference
    latest_league_id = league_ids[0] 

    # Database path
    db_path = '/Users/jackoconnor/Desktop/Football/sleeper.db'

    # Connect to the database and process each league
    with sqlite3.connect(db_path) as conn:
        curr_league = latest_league_id
        while curr_league is not None:
            print(f"Processing league: {curr_league}")
            curr_league = process_league(curr_league, conn)

if __name__ == "__main__":
    main()