import sqlite3
import json
from sleeper_api import get_league, get_league_users, get_matchups, get_rosters, get_user_data, get_draft, get_draft_picks

def parse_record(record_str):
    """
    Parse a record string like "WWLWWWWWWWLLWW" into wins, losses, ties.
    Returns (wins, losses, ties) as integers.
    """
    if not record_str:
        return 0, 0, 0
    
    wins = record_str.count('W')
    losses = record_str.count('L')
    ties = record_str.count('T')  # In case there are ties in the future
    
    return wins, losses, ties

def process_draft_data(draft_id, league_id, season, cursor):
    """
    Process draft data and insert into Draft and DraftPick tables.
    """
    try:
        draft = get_draft(draft_id)
        draft_picks = get_draft_picks(draft_id)
        
        # Insert draft record
        draft_qry = '''
            INSERT OR REPLACE INTO Draft (DraftID, LeagueID, Season, Type, Status, StartTime, EndTime, Settings, JSONData)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        cursor.execute(draft_qry, (
            draft_id,
            league_id,
            season,
            draft.get("type"),
            draft.get("status"),
            draft.get("start_time"),
            draft.get("end_time"),
            json.dumps(draft.get("settings", {})),
            json.dumps(draft)
        ))
        
        # Insert draft picks
        if draft_picks:
            draft_pick_qry = '''
                INSERT OR REPLACE INTO DraftPick (DraftID, LeagueID, Season, Round, Pick, RosterCode, PlayerID, PickTime, JSONData)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            picks_data = []
            for pick in draft_picks:
                picks_data.append((
                    draft_id,
                    league_id,
                    season,
                    pick.get("round"),
                    pick.get("pick_no"),
                    pick.get("roster_id"),
                    pick.get("player_id"),
                    pick.get("picked_at"),
                    json.dumps(pick)
                ))
            cursor.executemany(draft_pick_qry, picks_data)
            
    except Exception as e:
        print(f"Error processing draft data for {draft_id}: {e}")

def calculate_weekly_stats(league_id, season, cursor):
    """
    Calculate and insert weekly stats from matchup data.
    """
    # Get all matchup roster data for this league/season
    cursor.execute('''
        SELECT mr.RosterCode, mr.Week, mr.Points, mr.IsWinner, m.IsPlayoff,
               mr2.Points as OpponentPoints, mr2.RosterCode as OpponentRosterCode
        FROM MatchupRoster mr
        JOIN Matchup m ON mr.MatchupID = m.MatchupID
        LEFT JOIN MatchupRoster mr2 ON mr.MatchupID = mr2.MatchupID AND mr.RosterCode != mr2.RosterCode
        WHERE mr.LeagueID = ? AND mr.Season = ?
        ORDER BY mr.RosterCode, mr.Week
    ''', (league_id, season))
    
    weekly_data = cursor.fetchall()
    
    # Group by roster and week
    roster_week_stats = {}
    for row in weekly_data:
        roster_code, week, points, is_winner, is_playoff, opp_points, opp_roster = row
        key = (roster_code, week)
        
        if key not in roster_week_stats:
            roster_week_stats[key] = {
                'roster_code': roster_code,
                'week': week,
                'points': points or 0,
                'points_against': opp_points or 0,
                'win': is_winner or 0,
                'loss': 1 - (is_winner or 0) if points is not None else 0,
                'tie': 0,  # Sleeper doesn't support ties typically
                'opponent_roster': opp_roster,
                'is_playoff': is_playoff or 0
            }
    
    # Insert weekly stats
    weekly_stats_qry = '''
        INSERT OR REPLACE INTO WeeklyStats (RosterCode, LeagueID, Season, Week, Points, PointsAgainst, Win, Loss, Tie, OpponentRosterCode, IsPlayoff)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    
    stats_data = []
    for stats in roster_week_stats.values():
        stats_data.append((
            stats['roster_code'],
            league_id,
            season,
            stats['week'],
            stats['points'],
            stats['points_against'],
            stats['win'],
            stats['loss'],
            stats['tie'],
            stats['opponent_roster'],
            stats['is_playoff']
        ))
    
    if stats_data:
        cursor.executemany(weekly_stats_qry, stats_data)

def calculate_season_stats(league_id, season, cursor):
    """
    Calculate and insert season stats from weekly stats.
    """
    # Get aggregated stats for each roster
    cursor.execute('''
        SELECT 
            RosterCode,
            SUM(Points) as TotalPoints,
            SUM(PointsAgainst) as TotalPointsAgainst,
            SUM(Win) as Wins,
            SUM(Loss) as Losses,
            SUM(Tie) as Ties,
            SUM(CASE WHEN IsPlayoff = 0 THEN Win ELSE 0 END) as RegularSeasonWins,
            SUM(CASE WHEN IsPlayoff = 0 THEN Loss ELSE 0 END) as RegularSeasonLosses,
            SUM(CASE WHEN IsPlayoff = 1 THEN Win ELSE 0 END) as PlayoffWins,
            SUM(CASE WHEN IsPlayoff = 1 THEN Loss ELSE 0 END) as PlayoffLosses,
            COUNT(*) as GamesPlayed
        FROM WeeklyStats
        WHERE LeagueID = ? AND Season = ?
        GROUP BY RosterCode
    ''', (league_id, season))
    
    season_data = cursor.fetchall()
    
    # Calculate derived stats and insert
    season_stats_qry = '''
        INSERT OR REPLACE INTO SeasonStats (RosterCode, LeagueID, Season, TotalPoints, TotalPointsAgainst, Wins, Losses, Ties, WinPercentage, PointsPerGame, PointsAgainstPerGame, PointDifferential, RegularSeasonWins, RegularSeasonLosses, PlayoffWins, PlayoffLosses)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    
    stats_data = []
    for row in season_data:
        roster_code, total_points, total_against, wins, losses, ties, reg_wins, reg_losses, playoff_wins, playoff_losses, games = row
        
        if games > 0:
            win_pct = (wins + 0.5 * ties) / games if games > 0 else 0
            points_per_game = total_points / games
            points_against_per_game = total_against / games
            point_diff = total_points - total_against
        else:
            win_pct = 0
            points_per_game = 0
            points_against_per_game = 0
            point_diff = 0
        
        stats_data.append((
            roster_code,
            league_id,
            season,
            total_points,
            total_against,
            wins,
            losses,
            ties,
            win_pct,
            points_per_game,
            points_against_per_game,
            point_diff,
            reg_wins,
            reg_losses,
            playoff_wins,
            playoff_losses
        ))
    
    if stats_data:
        cursor.executemany(season_stats_qry, stats_data)

def load_players_data(conn):
    """
    Load all NFL players data into the Player table.
    This should be run once or periodically to keep player data updated.
    """
    try:
        from sleeper_api import get_players
        players = get_players()
        
        player_qry = '''
            INSERT OR REPLACE INTO Player (PlayerID, FirstName, LastName, FullName, Team, Position, Status, InjuryStatus, Age, Height, Weight, College, YearsExp, SearchRank, JSONData)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        players_data = []
        for player_id, player_data in players.items():
            first_name = player_data.get("first_name", "")
            last_name = player_data.get("last_name", "")
            full_name = f"{first_name} {last_name}".strip()
            
            players_data.append((
                player_id,
                first_name,
                last_name,
                full_name,
                player_data.get("team"),
                player_data.get("position"),
                player_data.get("status"),
                player_data.get("injury_status"),
                player_data.get("age"),
                player_data.get("height"),
                player_data.get("weight"),
                player_data.get("college"),
                player_data.get("years_exp"),
                player_data.get("search_rank"),
                json.dumps(player_data)
            ))
        
        cursor = conn.cursor()
        cursor.executemany(player_qry, players_data)
        conn.commit()
        print(f"Loaded {len(players_data)} players into database")
        
    except Exception as e:
        print(f"Error loading players data: {e}")

def process_league(league_id, conn):
    """
    Processes and inserts all data related to a single league into the database.
    """
    cursor = conn.cursor()

    # LEAGUE
    league = get_league(league_id)
    league_qry = '''
        INSERT OR REPLACE INTO League (LeagueID, Season, Name, Previous_League_ID, DraftID, Status, Settings, ScoringSettings, RosterPositions, JSONData)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    league_data = (
        league["league_id"],
        league["season"],
        league["name"],
        league.get("previous_league_id"),
        league.get("draft_id"),
        league.get("status", "complete"),
        json.dumps(league.get("settings", {})),
        json.dumps(league.get("scoring_settings", {})),
        json.dumps(league.get("roster_positions", [])),
        json.dumps(league),
    )
    cursor.execute(league_qry, league_data)

    # USERS
    league_users = get_league_users(league_id)
    team_data = {}
    user_qry = '''
        INSERT OR REPLACE INTO User (UserID, UserName, DisplayName, Avatar, JSONData)
        VALUES (?, ?, ?, ?, ?)
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
            user_data.get("avatar"),
            json.dumps(user_data),
        ))
    cursor.executemany(user_qry, users_data)

    # TEAMS
    rosters = get_rosters(league_id)
    
    # Debug: Check what we're getting
    print(f"Total rosters returned: {len(rosters) if rosters else 0}")
    print(f"Rosters type: {type(rosters)}")
    
    if rosters:
        for i, roster in enumerate(rosters):
            print(f"Roster {i}: {type(roster)} - {roster is None}")
            if roster is not None:
                print(f"  - roster_id: {roster.get('roster_id')}")
                print(f"  - owner_id: {roster.get('owner_id')}")
            else:
                print(f"  - This roster is None!")
    
    teams_qry = '''
        INSERT OR REPLACE INTO Team (UserID, RosterCode, LeagueID, Season, TeamName, Record, Streak, Fpts, FptsAgainst, Wins, Losses, Ties, JSONData)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    teams_data = []
    if rosters:  # Check if rosters is not None/empty
        for i, data in enumerate(rosters):
            if data is None:
                print(f"Warning: Roster at index {i} is None, skipping")
                continue
                
            # Additional safety checks
            if not isinstance(data, dict):
                print(f"Warning: Roster at index {i} is not a dict: {type(data)}, skipping")
                continue
                
            owner_id = data.get('owner_id')
            roster_id = data.get('roster_id')
            
            if not owner_id or not roster_id:
                print(f"Warning: Roster at index {i} missing owner_id or roster_id, skipping")
                continue
                
            team_name = team_data.get(owner_id, 'unknown')
            metadata = data.get("metadata", {}) or {}
            settings = data.get("settings", {}) or {}
            record = metadata.get("record", "")
            wins, losses, ties = parse_record(record)
            
            teams_data.append((
                owner_id,
                roster_id,
                league_id,
                league["season"],
                team_name,
                record,
                metadata.get("streak"),
                settings.get("fpts", 0),
                settings.get("fpts_against", 0),
                wins,
                losses,
                ties,
                json.dumps(data),
            ))
    
    if teams_data:
        cursor.executemany(teams_qry, teams_data)
        print(f"Successfully processed {len(teams_data)} teams")
    else:
        print("Warning: No valid team data to process")

    # MATCHUPS - Process with new schema
    matchups = get_matchups(league_id)
    
    # First, create Matchup records
    matchup_qry = '''
        INSERT OR REPLACE INTO Matchup (LeagueID, Season, Week, MatchupCode, PlayoffRound, IsPlayoff, JSONData)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    '''
    
    # Group matchups by week and matchup_id to create unique Matchup records
    matchup_groups = {}
    for data in matchups:
        week = data["week"]
        matchup_id = data.get("matchup_id")
        key = (week, matchup_id)
        
        if key not in matchup_groups:
            # Determine if it's a playoff matchup (typically weeks 15+)
            is_playoff = 1 if week >= 15 else 0
            playoff_round = None
            if is_playoff:
                playoff_round = week - 14  # Simple playoff round calculation
            
            matchup_groups[key] = {
                'week': week,
                'matchup_id': matchup_id,
                'is_playoff': is_playoff,
                'playoff_round': playoff_round,
                'rosters': []
            }
        
        matchup_groups[key]['rosters'].append(data)
    
    # Insert Matchup records
    matchup_data = []
    for key, matchup_info in matchup_groups.items():
        # Skip if MatchupCode is None (eliminated teams in playoffs)
        if matchup_info['matchup_id'] is None:
            print(f"Warning: Skipping matchup with None MatchupCode for week {matchup_info['week']}")
            continue
        
        matchup_data.append((
            league_id,
            league["season"],
            matchup_info['week'],
            matchup_info['matchup_id'],
            matchup_info['playoff_round'],
            matchup_info['is_playoff'],
            json.dumps(matchup_info)
        ))
    cursor.executemany(matchup_qry, matchup_data)
    
    # Now create MatchupRoster records
    matchup_roster_qry = '''
        INSERT OR REPLACE INTO MatchupRoster (MatchupID, RosterCode, LeagueID, Season, Week, Points, ProjectedPoints, IsWinner, JSONData)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    
    matchup_roster_data = []
    for key, matchup_info in matchup_groups.items():
        # Get the MatchupID for this matchup
        cursor.execute('''
            SELECT MatchupID FROM Matchup 
            WHERE LeagueID = ? AND Week = ? AND MatchupCode = ?
        ''', (league_id, matchup_info['week'], matchup_info['matchup_id']))
        matchup_result = cursor.fetchone()
        if not matchup_result:
            continue
        matchup_id = matchup_result[0]
        
        # Process each roster in the matchup
        rosters = matchup_info['rosters']
        points_list = [r["points"] for r in rosters if r["points"] is not None]
        
        for roster in rosters:
            # Determine winner (highest points wins)
            is_winner = 0
            if roster["points"] is not None and points_list:
                max_points = max(points_list)
                if roster["points"] == max_points and len([p for p in points_list if p == max_points]) == 1:
                    is_winner = 1
            
            matchup_roster_data.append((
                matchup_id,
                roster["roster_id"],
                league_id,
                league["season"],
                roster["week"],
                roster["points"] or 0,
                roster.get("projected_points"),
                is_winner,
                json.dumps(roster)
            ))
    
    cursor.executemany(matchup_roster_qry, matchup_roster_data)
    
    # Process draft data if available
    if league.get("draft_id"):
        process_draft_data(league["draft_id"], league_id, league["season"], cursor)
    
    # Calculate and insert weekly stats
    calculate_weekly_stats(league_id, league["season"], cursor)
    
    # Calculate and insert season stats
    calculate_season_stats(league_id, league["season"], cursor)

    conn.commit()
    return league["previous_league_id"]


def main():
    # List of league IDs to process
    # league_ids = ['1120774194318479360', '868563615295410176', '990267272524541952'] # new to old, here for reference
    latest_league_id = '1219656680917176320'

    # Database path
    db_path = '/Users/jackoconnor/Desktop/Football/sleeper.db'

    # Connect to the database and process each league
    with sqlite3.connect(db_path) as conn:
        try:
            # Optionally load players data first (uncomment if needed)
            # print("Loading players data...")
            # load_players_data(conn)
            
            curr_league = latest_league_id
            while curr_league is not None:
                try:
                    print(f"Processing league: {curr_league}")
                    curr_league = process_league(curr_league, conn)
                    print(f"Successfully processed league: {curr_league}")
                except Exception as e:
                    print(f"Error processing league {curr_league}: {e}")
                    raise(e)
                    break
                    
        except Exception as e:
            print(f"Database error: {e}")
            raise(e)
        finally:
            print("Processing complete.")

if __name__ == "__main__":
    main()