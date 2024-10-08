import sqlite3
import json

from sleeper_api import get_league, get_league_users, get_matchups, get_players, get_rosters, get_user_data

LEAGUE_ID = '1120774194318479360'
# Old to New:
# 868563615295410176
# 990267272524541952
# 1120774194318479360

if __name__ == "__main__":
    # all_players= get_players()
    # player_qry = 'INSERT INTO Player (PlayerID, Team, Position, InjuryStatus, LastName, FirstName) VALUES'
    # for i,data in enumerate(all_players.values()):
    #     data['last_name'] = data['last_name'].replace("'", "''")
    #     data['first_name'] = data['first_name'].replace("'", "''")
    #     if data['position'] == "DEF" or data['injury_status'] is None:
    #         data['injury_status'] = 'Healthy'
    #     position = '|'.join(data['fantasy_positions']) if data['fantasy_positions'] is not None else ''
    #     player_qry += f'(\'{data["player_id"]}\',\'{data["team"]}\', \'{position}\',\'{data["injury_status"]}\',\'{data["last_name"]}\',\'{data["first_name"]}\')'
    #     if i != len(all_players) - 1:
    #         player_qry += ','


    league = get_league(LEAGUE_ID)
    league_qry = 'INSERT INTO League (LeagueID, Season, JSONData, Previous_League_ID, Name, DraftID) VALUES ' 
    league_qry += f'(\'{league["league_id"]}\',\'{league["season"]}\',\'{json.dumps(league)}\',\'{league["previous_league_id"]}\',\'{league["name"]}\',\'{league["draft_id"]}\')'

    league_users = get_league_users(LEAGUE_ID)
    team_data = {}
    user_qry = 'INSERT OR IGNORE INTO [User] (UserID, UserName, DisplayName, JSONData) VALUES '
    for i, data in enumerate(league_users):
        if not data.get("metadata") or not data["metadata"].get("team_name"): 
            team_name = ''
        else:
            team_name = data["metadata"]["team_name"]
        team_data[data["user_id"]] = team_name
        user_data = get_user_data(data["user_id"])
        user_qry += f'(\'{user_data["user_id"]}\',\'{user_data["username"]}\',\'{user_data["display_name"]}\',\'{json.dumps(user_data)}\')'
        if i != len(league_users) - 1:
            user_qry += ','

        
    rosters = get_rosters(LEAGUE_ID)
    teams_qry = 'INSERT INTO Team (UserID, RosterCode, LeagueID, TeamName, Record, Streak, Fpts, FptsAgainst) VALUES '
    # roster_player_qry = 'INSERT INTO RosterPlayer (RosterPlayerID, RosterID, PlayerID, Starter) VALUES '
    for i, data in enumerate(rosters):
        if not data.get('owner_id'):
            team_name = 'unknown'
            data['owner_id'] = 'unknown'
        else:
            team_name = team_data[data['owner_id']]
        teams_qry += f'(\'{data["owner_id"]}\',\'{data["roster_id"]}\',\'{LEAGUE_ID}\', \'{team_name}\',\'{data["metadata"]["record"]}\',\'{data["metadata"]["streak"]}\',{data["settings"]["fpts"]}, {data["settings"]["fpts_against"]})'
        if i != len(rosters) - 1:
            teams_qry += ','

    #     starters = set(data['starters'])
    #     for j, player_id in enumerate(data['players']):
    #         roster_player_qry += f'({i*len(data["players"])+j},\'{data["roster_id"]}\',\'{player_id}\',{1 if player_id in starters else 0})'
    #         if i != len(rosters) - 1 or j != len(data['players']) - 1:
    #             roster_player_qry += ','

    matchups = get_matchups(LEAGUE_ID)
    
    matchup_roster_qry = 'INSERT INTO MatchupRoster (LeagueID, MatchupCode, RosterCode, Week, Points) \n VALUES '
    for i, data in enumerate(matchups):
        if data["matchup_id"] is None:
            data["matchup_id"] = 'NULL'
        else:
            data["matchup_id"] = '\'' + str(data["matchup_id"])+'\''
        matchup_roster_qry += f'(\'{LEAGUE_ID}\',{data["matchup_id"]}, {data["roster_id"]}, {data["week"]},{data["points"]})'
        if i != len(matchups) - 1:
            matchup_roster_qry += ','

    league_qry += ';'
    user_qry += ';'
    teams_qry += ';'
    matchup_roster_qry += ';'

    with sqlite3.connect('/Users/jackoconnor/Desktop/Football/sleeper.db') as conn:
        cursor = conn.cursor()
        try:
            # cursor.execute(player_qry)
            cursor.execute(league_qry)
            cursor.execute(user_qry)
            cursor.execute(teams_qry)
            cursor.execute(matchup_roster_qry)
            conn.commit()
        finally:
            cursor.close()
