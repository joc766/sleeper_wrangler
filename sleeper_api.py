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

def get_draft(draft_id):
    """Get draft information including picks and rounds"""
    url = 'https://api.sleeper.app/v1/draft/' + draft_id
    response = requests.get(url)
    
    response.raise_for_status()
    
    data = response.json()
    return data

def get_draft_picks(draft_id):
    """Get all picks from a specific draft"""
    url = 'https://api.sleeper.app/v1/draft/' + draft_id + '/picks'
    response = requests.get(url)
    
    response.raise_for_status()
    
    data = response.json()
    return data

def get_adp_data():
    """Get current ADP (Average Draft Position) data"""
    # Note: Sleeper doesn't have a public ADP API, so we'll use search_rank as a proxy
    # In a real implementation, you might want to scrape ADP from sites like FantasyPros
    url = 'https://api.sleeper.app/v1/players/nfl'
    response = requests.get(url)
    
    response.raise_for_status()
    
    data = response.json()
    
    # Extract ADP-like data from search_rank
    adp_data = {}
    for player_id, player in data.items():
        if player.get('search_rank') and player.get('search_rank') != 9999:
            # Convert search_rank to approximate ADP
            # Lower search_rank = higher ADP (better player)
            # We'll use search_rank directly as a rough ADP approximation
            # In a 10-team league with 17 rounds, max ADP would be around 170
            search_rank = player.get('search_rank')
            
            # Convert to approximate round (assuming 10 teams, 17 rounds)
            # This is a rough approximation - in reality you'd want actual ADP data
            approximate_round = max(1, min(17, (search_rank // 10) + 1))
            
            adp_data[player_id] = {
                'adp': approximate_round,
                'search_rank': search_rank,
                'position': player.get('position'),
                'name': f"{player.get('first_name', '')} {player.get('last_name', '')}".strip()
            }
    
    return adp_data

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
