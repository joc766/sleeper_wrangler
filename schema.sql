-- Improved Fantasy Football Schema for SQLite
-- Based on analysis of current queries and Sleeper API data structure

-- =============================================
-- CORE ENTITIES
-- =============================================

-- Users table
CREATE TABLE User (
  UserID TEXT PRIMARY KEY,
  UserName TEXT NOT NULL,
  DisplayName TEXT,
  Avatar TEXT,
  JSONData TEXT,
  
  UNIQUE(UserName)
);

-- Leagues table (enhanced)
CREATE TABLE League (
  LeagueID TEXT PRIMARY KEY,
  Season TEXT NOT NULL,
  Name TEXT NOT NULL,
  Previous_League_ID TEXT,
  DraftID TEXT,
  Status TEXT, -- 'in_season', 'complete', 'drafting', etc.
  Settings TEXT, -- JSON for league settings
  ScoringSettings TEXT, -- JSON for scoring rules
  RosterPositions TEXT, -- JSON for roster requirements
  JSONData TEXT
);

-- Teams table (enhanced with better indexing)
CREATE TABLE Team (
  TeamID INTEGER PRIMARY KEY AUTOINCREMENT,
  RosterCode INTEGER NOT NULL,
  UserID TEXT NOT NULL,
  LeagueID TEXT NOT NULL,
  Season TEXT NOT NULL, -- Denormalized for performance
  TeamName TEXT,
  Record TEXT,
  Streak TEXT,
  Fpts REAL DEFAULT 0,
  FptsAgainst REAL DEFAULT 0,
  Wins INTEGER DEFAULT 0,
  Losses INTEGER DEFAULT 0,
  Ties INTEGER DEFAULT 0,
  JSONData TEXT,
  
  UNIQUE(UserID, LeagueID),
  UNIQUE(LeagueID, Season, RosterCode),
  FOREIGN KEY (UserID) REFERENCES User(UserID),
  FOREIGN KEY (LeagueID) REFERENCES League(LeagueID)
);

-- =============================================
-- MATCHUP SYSTEM (IMPROVED)
-- =============================================

-- Matchups table (new - represents the actual matchup between teams)
CREATE TABLE Matchup (
  MatchupID INTEGER PRIMARY KEY AUTOINCREMENT,
  LeagueID TEXT NOT NULL,
  Season TEXT NOT NULL, -- Denormalized for performance
  Week INTEGER NOT NULL,
  MatchupCode INTEGER NOT NULL, -- Original Sleeper matchup_id
  PlayoffRound INTEGER, -- For playoff matchups
  IsPlayoff INTEGER DEFAULT 0, -- SQLite uses INTEGER for boolean
  JSONData TEXT,
  
  UNIQUE(LeagueID, Season, Week, MatchupCode),
  FOREIGN KEY (LeagueID) REFERENCES League(LeagueID)
);

-- MatchupRoster table (simplified and optimized)
CREATE TABLE MatchupRoster (
  MatchupRosterID INTEGER PRIMARY KEY AUTOINCREMENT,
  MatchupID INTEGER NOT NULL, -- FK to Matchup table
  RosterCode INTEGER NOT NULL,
  LeagueID TEXT NOT NULL, -- Denormalized for performance
  Season TEXT NOT NULL, -- Denormalized for performance
  Week INTEGER NOT NULL, -- Denormalized for performance
  Points REAL DEFAULT 0,
  ProjectedPoints REAL,
  IsWinner INTEGER, -- Pre-calculated for performance (SQLite boolean)
  JSONData TEXT,
  
  UNIQUE(MatchupID, RosterCode),
  UNIQUE(LeagueID, Season, Week, RosterCode),
  FOREIGN KEY (MatchupID) REFERENCES Matchup(MatchupID),
  FOREIGN KEY (LeagueID) REFERENCES League(LeagueID)
);

-- =============================================
-- PLAYER SYSTEM (ENHANCED)
-- =============================================

-- Players table (enhanced)
CREATE TABLE Player (
  PlayerID TEXT PRIMARY KEY,
  FirstName TEXT,
  LastName TEXT,
  FullName TEXT NOT NULL, -- Computed column for performance
  Team TEXT,
  Position TEXT NOT NULL,
  Status TEXT, -- 'Active', 'Injured', 'Suspended', etc.
  InjuryStatus TEXT,
  Age INTEGER,
  Height TEXT,
  Weight INTEGER,
  College TEXT,
  YearsExp INTEGER,
  SearchRank INTEGER, -- For ADP calculations
  JSONData TEXT
);

-- MatchupRosterPlayer table
CREATE TABLE MatchupRosterPlayer (
  MatchupRosterPlayerID INTEGER PRIMARY KEY AUTOINCREMENT,
  MatchupRosterID INTEGER NOT NULL,
  PlayerID TEXT NOT NULL,
  Position TEXT NOT NULL,
  Starter INTEGER NOT NULL DEFAULT 0, -- SQLite boolean
  Points REAL DEFAULT 0,
  ProjectedPoints REAL,
  JSONData TEXT,
  
  UNIQUE(MatchupRosterID, PlayerID),
  FOREIGN KEY (MatchupRosterID) REFERENCES MatchupRoster(MatchupRosterID),
  FOREIGN KEY (PlayerID) REFERENCES Player(PlayerID)
);

-- =============================================
-- PERFORMANCE TABLES (NEW)
-- =============================================

-- WeeklyStats table (pre-calculated for performance)
CREATE TABLE WeeklyStats (
  WeeklyStatsID INTEGER PRIMARY KEY AUTOINCREMENT,
  RosterCode INTEGER NOT NULL,
  LeagueID TEXT NOT NULL,
  Season TEXT NOT NULL,
  Week INTEGER NOT NULL,
  Points REAL NOT NULL,
  PointsAgainst REAL NOT NULL,
  Win INTEGER NOT NULL, -- SQLite boolean
  Loss INTEGER NOT NULL, -- SQLite boolean
  Tie INTEGER NOT NULL, -- SQLite boolean
  OpponentRosterCode INTEGER,
  IsPlayoff INTEGER DEFAULT 0, -- SQLite boolean
  CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
  
  UNIQUE(RosterCode, Season, Week),
  FOREIGN KEY (LeagueID) REFERENCES League(LeagueID)
);

-- SeasonStats table (pre-calculated season totals)
CREATE TABLE SeasonStats (
  SeasonStatsID INTEGER PRIMARY KEY AUTOINCREMENT,
  RosterCode INTEGER NOT NULL,
  LeagueID TEXT NOT NULL,
  Season TEXT NOT NULL,
  TotalPoints REAL NOT NULL,
  TotalPointsAgainst REAL NOT NULL,
  Wins INTEGER NOT NULL,
  Losses INTEGER NOT NULL,
  Ties INTEGER NOT NULL,
  WinPercentage REAL NOT NULL,
  PointsPerGame REAL NOT NULL,
  PointsAgainstPerGame REAL NOT NULL,
  PointDifferential REAL NOT NULL,
  RegularSeasonWins INTEGER NOT NULL,
  RegularSeasonLosses INTEGER NOT NULL,
  PlayoffWins INTEGER DEFAULT 0,
  PlayoffLosses INTEGER DEFAULT 0,
  FinalRank INTEGER,
  CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
  UpdatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
  
  UNIQUE(RosterCode, Season),
  FOREIGN KEY (LeagueID) REFERENCES League(LeagueID)
);

-- =============================================
-- DRAFT SYSTEM (NEW)
-- =============================================

-- Drafts table
CREATE TABLE Draft (
  DraftID TEXT PRIMARY KEY,
  LeagueID TEXT NOT NULL,
  Season TEXT NOT NULL,
  Type TEXT, -- 'snake', 'linear', 'auction'
  Status TEXT, -- 'pre_draft', 'in_progress', 'complete'
  StartTime DATETIME,
  EndTime DATETIME,
  Settings TEXT, -- JSON for draft settings
  JSONData TEXT,
  
  UNIQUE(LeagueID, Season),
  FOREIGN KEY (LeagueID) REFERENCES League(LeagueID)
);

-- DraftPicks table
CREATE TABLE DraftPick (
  DraftPickID INTEGER PRIMARY KEY AUTOINCREMENT,
  DraftID TEXT NOT NULL,
  LeagueID TEXT NOT NULL, -- Denormalized
  Season TEXT NOT NULL, -- Denormalized
  Round INTEGER NOT NULL,
  Pick INTEGER NOT NULL,
  RosterCode INTEGER NOT NULL,
  PlayerID TEXT NOT NULL,
  PickTime DATETIME,
  JSONData TEXT,
  
  UNIQUE(DraftID, Round, Pick),
  FOREIGN KEY (DraftID) REFERENCES Draft(DraftID),
  FOREIGN KEY (PlayerID) REFERENCES Player(PlayerID)
);

-- =============================================
-- INDEXES FOR PERFORMANCE
-- =============================================

-- League indexes
CREATE INDEX idx_league_season_status ON League(Season, Status);
CREATE INDEX idx_league_previous ON League(Previous_League_ID);

-- Team indexes
CREATE INDEX idx_team_league_season ON Team(LeagueID, Season);
CREATE INDEX idx_team_season_points ON Team(Season, Fpts);

-- Matchup indexes
CREATE INDEX idx_matchup_league_week ON Matchup(LeagueID, Season, Week);
CREATE INDEX idx_matchup_season_week ON Matchup(Season, Week);

-- MatchupRoster indexes
CREATE INDEX idx_matchup_roster_league_season_week ON MatchupRoster(LeagueID, Season, Week);
CREATE INDEX idx_matchup_roster_season_week_points ON MatchupRoster(Season, Week, Points);
CREATE INDEX idx_matchup_roster_roster_season_week ON MatchupRoster(RosterCode, Season, Week);

-- Player indexes
CREATE INDEX idx_player_fullname ON Player(FullName);
CREATE INDEX idx_player_position_team ON Player(Position, Team);
CREATE INDEX idx_player_position_searchrank ON Player(Position, SearchRank);
CREATE INDEX idx_player_status ON Player(Status);

-- MatchupRosterPlayer indexes
CREATE INDEX idx_matchup_roster_player_roster_position_starter ON MatchupRosterPlayer(MatchupRosterID, Position, Starter);
CREATE INDEX idx_matchup_roster_player_player_position ON MatchupRosterPlayer(PlayerID, Position);

-- WeeklyStats indexes
CREATE INDEX idx_weekly_stats_league_season_week ON WeeklyStats(LeagueID, Season, Week);
CREATE INDEX idx_weekly_stats_season_week_points ON WeeklyStats(Season, Week, Points);
CREATE INDEX idx_weekly_stats_season_week_wins ON WeeklyStats(Season, Week, Win);

-- SeasonStats indexes
CREATE INDEX idx_season_stats_league_season_rank ON SeasonStats(LeagueID, Season, FinalRank);
CREATE INDEX idx_season_stats_season_total_points ON SeasonStats(Season, TotalPoints);
CREATE INDEX idx_season_stats_season_win_pct ON SeasonStats(Season, WinPercentage);

-- Draft indexes
CREATE INDEX idx_draft_season_status ON Draft(Season, Status);

-- DraftPick indexes
CREATE INDEX idx_draft_pick_league_season_roster ON DraftPick(LeagueID, Season, RosterCode);
CREATE INDEX idx_draft_pick_player_season ON DraftPick(PlayerID, Season);

-- =============================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- =============================================

-- Trigger to update FullName when FirstName or LastName changes
CREATE TRIGGER update_player_fullname 
AFTER UPDATE OF FirstName, LastName ON Player
BEGIN
    UPDATE Player 
    SET FullName = TRIM(COALESCE(FirstName, '') || ' ' || COALESCE(LastName, ''))
    WHERE PlayerID = NEW.PlayerID;
END;

-- Trigger to update UpdatedDate when SeasonStats changes
CREATE TRIGGER update_season_stats_timestamp 
AFTER UPDATE ON SeasonStats
BEGIN
    UPDATE SeasonStats 
    SET UpdatedDate = CURRENT_TIMESTAMP
    WHERE SeasonStatsID = NEW.SeasonStatsID;
END;

-- =============================================
-- SAMPLE QUERIES THAT WOULD BENEFIT
-- =============================================

/*
-- Example: Regular Season Payout (much simpler with new schema)
SELECT 
    l.Season,
    u.UserName,
    t.TeamName,
    COUNT(*) * 10 AS TotalReward
FROM WeeklyStats ws
    JOIN Team t ON ws.RosterCode = t.RosterCode AND ws.LeagueID = t.LeagueID
    JOIN User u ON t.UserID = u.UserID
    JOIN League l ON ws.LeagueID = l.LeagueID
WHERE ws.Week <= 14 
    AND ws.Win = 1 
    AND l.Season = '2024'
    AND ws.IsPlayoff = 0
GROUP BY l.Season, u.UserName, t.TeamName
ORDER BY TotalReward DESC;

-- Example: Win Streaks (much more efficient)
WITH WinStreaks AS (
    SELECT 
        u.UserName,
        l.Season,
        ws.Week,
        ws.Win,
        ROW_NUMBER() OVER (PARTITION BY u.UserName ORDER BY l.Season, ws.Week) 
            - ROW_NUMBER() OVER (PARTITION BY u.UserName, ws.Win ORDER BY l.Season, ws.Week) AS win_group
    FROM WeeklyStats ws
        JOIN Team t ON ws.RosterCode = t.RosterCode
        JOIN User u ON t.UserID = u.UserID
        JOIN League l ON ws.LeagueID = l.LeagueID
    WHERE ws.Win = 1
)
SELECT 
    UserName,
    Season,
    MIN(Week) AS start_week,
    MAX(Week) AS end_week,
    COUNT(*) AS streak_length
FROM WinStreaks
GROUP BY UserName, Season, win_group
ORDER BY streak_length DESC;

-- Example: Point Totals (simplified)
SELECT 
    ROW_NUMBER() OVER (ORDER BY mr1.Points + mr2.Points DESC) AS Rank,
    l.Season,
    mr1.Week,
    u1.UserName AS 'Player 1',
    mr1.Points,
    u2.UserName AS 'Player 2', 
    mr2.Points,
    mr1.Points + mr2.Points AS 'Total Points'
FROM MatchupRoster mr1
    JOIN MatchupRoster mr2 ON mr1.MatchupID = mr2.MatchupID AND mr1.Points > mr2.Points
    JOIN Team t1 ON mr1.RosterCode = t1.RosterCode
    JOIN Team t2 ON mr2.RosterCode = t2.RosterCode
    JOIN User u1 ON t1.UserID = u1.UserID
    JOIN User u2 ON t2.UserID = u2.UserID
    JOIN League l ON mr1.LeagueID = l.LeagueID
ORDER BY mr1.Points + mr2.Points DESC;
*/
