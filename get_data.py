import requests
import sqlite3
import json

LEAGUE_ID = '990267272524541952'

def create_database(db_name, schema_path):

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    with open(schema_path, 'r') as file:
        sql_script = file.read()
    try:
        cursor.executescript(sql_script)
        conn.commit()
        print("SQLite database has been created successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the connection
        conn.close()

def get_players():
    url = 'https://api.sleeper.app/v1/players/nfl'
    response = requests.get(url)
    
    response.raise_for_status()

    data = response.json()

    return data



def get_league(leagueid):
    url = 'https://api.sleeper.app/v1/league/' + leagueid
    response = requests.get(url)
    
    response.raise_for_status()

    data = response.json()

    return data

def get_league_users(leagueid):
    url = 'https://api.sleeper.app/v1/league/' + leagueid + '/users'
    response = requests.get(url)
    
    response.raise_for_status()

    data = response.json()

    return data

def get_rosters(leagueid):
    url = 'https://api.sleeper.app/v1/league/' + leagueid + '/rosters'
    response = requests.get(url)
    
    response.raise_for_status()

    data = response.json()

    return data

def get_user_data(userID):
    url = 'https://api.sleeper.app/v1/user/' + userID
    response = requests.get(url)
    
    response.raise_for_status()

    data = response.json()

    return data


if __name__ == "__main__":
    # db_name = 'sleeper.db'
    # schema_path = '/Users/jackoconnor/Desktop/Football/sleeper.sql'
    # create_database(db_name, schema_path)
    # exit(0)

    all_players= get_players()
    player_qry = 'INSERT INTO Player (PlayerID, Team, Position, InjuryStatus, LastName, FirstName) VALUES'
    for i,data in enumerate(all_players.values()):
        data['last_name'] = data['last_name'].replace("'", "''")
        data['first_name'] = data['first_name'].replace("'", "''")
        if data['position'] == "DEF" or data['injury_status'] is None:
            data['injury_status'] = 'Healthy'
        position = '|'.join(data['fantasy_positions']) if data['fantasy_positions'] is not None else ''
        player_qry += f'(\'{data["player_id"]}\',\'{data["team"]}\', \'{position}\',\'{data["injury_status"]}\',\'{data["last_name"]}\',\'{data["first_name"]}\')'
        if i != len(all_players) - 1:
            player_qry += ','


    league = get_league(LEAGUE_ID)
    league_qry = 'INSERT INTO League (LeagueID, Season, JSONData, Previous_League_ID, Name, DraftID) ' 
    league_qry = f'VALUES (\'{league["league_id"]}\',\'{league["season"]}\',\'{json.dumps(league)}\',\'{league["previous_league_id"]}\',\'{league["name"]}\',\'{league["draft_id"]}\')'


    league_users = get_league_users(LEAGUE_ID)
    league_user_qry = 'INSERT INTO LeagueUser (LeagueUserID, UserID, LeagueID, TeamName, AvatarID) VALUES '
    user_qry = 'INSERT INTO [User] (UserID, UserName, DisplayName, JSONData) VALUES '
    for i, data in enumerate(league_users):
        league_user_qry += f'({i}, \'{data["user_id"]}\',\'{data["league_id"]}\',\'{data["metadata"]["team_name"]}\',\'{data["avatar"]}\')'
        user_data = get_user_data(data["user_id"])
        user_qry += f'(\'{user_data["user_id"]}\',\'{user_data["username"]}\',\'{user_data["display_name"]}\',\'{json.dumps(user_data)}\')'
        if i != len(league_users) - 1:
            league_user_qry += ','
            user_qry += ','

        
    rosters = get_rosters(LEAGUE_ID)
    roster_qry = 'INSERT INTO Roster (RosterID, OwnerID, Record, Streak, Fpts, FptsAgainst) VALUES '
    roster_player_qry = 'INSERT INTO RosterPlayer (RosterPlayerID, RosterID, PlayerID, Starter) VALUES '
    for i, data in enumerate(rosters):
        roster_qry += f'({data["roster_id"]},\'{data["owner_id"]}\',\'{data["metadata"]["record"]}\',\'{data["metadata"]["streak"]}\',{data["settings"]["fpts"]}, {data["settings"]["fpts_against"]})'
        if i != len(rosters) - 1:
            roster_qry += ','

        starters = set(data['starters'])
        for j, player_id in enumerate(data['players']):
            roster_player_qry += f'({i*len(data["players"])+j},\'{data["roster_id"]}\',\'{player_id}\',{1 if player_id in starters else 0})'
            if i != len(rosters) - 1 or j != len(data['players']) - 1:
                roster_player_qry += ','

    with sqlite3.connect('/Users/jackoconnor/Desktop/Football/sleeper.db') as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(player_qry)
            # cursor.execute(league_qry)
            # cursor.execute(league_user_qry)
            # cursor.execute(user_qry)
            # cursor.execute(roster_qry)
            # cursor.execute(roster_player_qry)
            conn.commit()
        finally:
            cursor.close()





