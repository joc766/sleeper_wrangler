import requests
import json

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

def get_matchups(leagueID):
    matchups = []
    i = 1
    while True:
        url = 'https://api.sleeper.app/v1/league/' + leagueID + '/matchups/' + str(i)
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if len(data) == 0:
            break
        for matchup in data:
            matchup['week'] = i
        matchups += data
        i += 1
    with open('refs/my-matchups.json', 'w') as f:
        json.dump(matchups, f)
    return matchups
