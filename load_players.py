from sleeper_api import get_players

def load_players():
    all_players= get_players()
    players_data = []
    for data in all_players.values():
        last_name = data['last_name'].replace("'", "''") if data['last_name'] else ''
        first_name = data['first_name'].replace("'", "''") if data['first_name'] else ''

        injury_status = data['injury_status'] if data['injury_status'] is not None else 'Healthy'
        
        position = '|'.join(data['fantasy_positions']) if data.get('fantasy_positions') else ''
        players_data.append((
            data["player_id"],
            data["team"],
            position,
            injury_status,
            last_name,
            first_name
        ))