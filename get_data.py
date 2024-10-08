import sqlite3
import json

from sleeper_api import get_league, get_league_users, get_matchups, get_rosters, get_user_data

LEAGUE_ID = '868563615295410176'
# Old to New:
# 868563615295410176
# 990267272524541952
# 1120774194318479360

if __name__ == "__main__":
    #############################
    # LEAGUE
    #############################
    league = get_league(LEAGUE_ID)
    league_qry = '''
        INSERT INTO League (LeagueID, Season, JSONData, Previous_League_ID, Name, DraftID)
        VALUES (?, ?, ?, ?, ?, ?)
    '''
    league_data = (
        league["league_id"],
        league["season"],
        json.dumps(league),  # JSON data, safely handled
        league["previous_league_id"],
        league["name"],
        league["draft_id"]
    )

    #############################
    # USERS
    #############################
    league_users = get_league_users(LEAGUE_ID)
    team_data = {}
    user_qry = '''
        INSERT OR IGNORE INTO [User] (UserID, UserName, DisplayName, JSONData)
        VALUES (?, ?, ?, ?)
    '''
    users_data = []
    for data in league_users:
        if not data.get("metadata") or not data["metadata"].get("team_name"): 
            team_name = ''
        else:
            team_name = data["metadata"]["team_name"]

        team_data[data["user_id"]] = team_name

        user_data = get_user_data(data["user_id"])

        users_data.append((
            user_data["user_id"],
            user_data["username"],
            user_data["display_name"],
            json.dumps(user_data)
        ))


    #############################
    # TEAMS
    #############################
    teams_data = []
    rosters = get_rosters(LEAGUE_ID)
    teams_qry = '''
        INSERT INTO Team (UserID, RosterCode, LeagueID, TeamName, Record, Streak, Fpts, FptsAgainst)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    '''
    # roster_player_qry = 'INSERT INTO RosterPlayer (RosterPlayerID, RosterID, PlayerID, Starter) VALUES '
    for i, data in enumerate(rosters):
        if not data.get('owner_id'):
            team_name = 'unknown'
            data['owner_id'] = 'unknown'
        else:
            team_name = team_data[data['owner_id']]

        teams_data.append((
            data["owner_id"],
            data["roster_id"],
            LEAGUE_ID,
            team_name,
            data["metadata"].get("record"),
            data["metadata"].get("streak"),
            data["settings"].get("fpts"),
            data["settings"].get("fpts_against")
        ))
    #     starters = set(data['starters'])
    #     for j, player_id in enumerate(data['players']):
    #         roster_player_qry += f'({i*len(data["players"])+j},\'{data["roster_id"]}\',\'{player_id}\',{1 if player_id in starters else 0})'
    #         if i != len(rosters) - 1 or j != len(data['players']) - 1:
    #             roster_player_qry += ','


    #############################
    # MATCHUPS
    #############################
    matchups = get_matchups(LEAGUE_ID)

    matchup_roster_qry = '''
        INSERT INTO MatchupRoster (LeagueID, MatchupCode, RosterCode, Week, Points)
        VALUES (?, ?, ?, ?, ?)
    '''
    matchups_data = []
    for data in matchups:
        matchup_id = data["matchup_id"] if data["matchup_id"] is not None else None
        matchups_data.append((
            LEAGUE_ID,
            matchup_id,
            data["roster_id"],
            data["week"],
            data["points"]
        ))


    with sqlite3.connect('/Users/jackoconnor/Desktop/Football/sleeper.db') as conn:
        cursor = conn.cursor()
        try:
            # cursor.execute(player_qry)
            cursor.execute(league_qry, league_data)
            cursor.executemany(user_qry, users_data)
            cursor.executemany(teams_qry, teams_data)
            cursor.executemany(matchup_roster_qry, matchups_data)
            conn.commit()
        finally:
            cursor.close()
