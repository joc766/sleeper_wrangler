-- Drop tables if they exist
IF OBJECT_ID('dbo.MatchupRosterPlayer', 'U') IS NOT NULL DROP TABLE dbo.MatchupRosterPlayer;
IF OBJECT_ID('dbo.Player', 'U') IS NOT NULL DROP TABLE dbo.Player;
IF OBJECT_ID('dbo.MatchupRoster', 'U') IS NOT NULL DROP TABLE dbo.MatchupRoster;
IF OBJECT_ID('dbo.Team', 'U') IS NOT NULL DROP TABLE dbo.Team;
IF OBJECT_ID('dbo.League', 'U') IS NOT NULL DROP TABLE dbo.League;
IF OBJECT_ID('dbo.[User]', 'U') IS NOT NULL DROP TABLE dbo.[User];

-- Create the User table
CREATE TABLE dbo.[User] (
    UserID NVARCHAR(255) PRIMARY KEY,
    UserName NVARCHAR(255),
    DisplayName NVARCHAR(255),
    JSONData NVARCHAR(MAX)
);

-- Create the League table
CREATE TABLE dbo.League (
    LeagueID NVARCHAR(255) PRIMARY KEY,
    Season NVARCHAR(255),
    JSONData NVARCHAR(MAX),
    Previous_League_ID NVARCHAR(255),
    Name NVARCHAR(255),
    DraftID NVARCHAR(255)
);

-- Create the Team table
CREATE TABLE dbo.Team (
    TeamID INT PRIMARY KEY,
    RosterCode INT,
    UserID NVARCHAR(255),
    LeagueID NVARCHAR(255),
    TeamName NVARCHAR(255),
    Record NVARCHAR(255),
    Streak NVARCHAR(255),
    Fpts DECIMAL(18, 2),
    FptsAgainst DECIMAL(18, 2),
    JSONData NVARCHAR(MAX),
    FOREIGN KEY (UserID) REFERENCES dbo.[User](UserID),
    FOREIGN KEY (LeagueID) REFERENCES dbo.League(LeagueID),
    CONSTRAINT unique_owner UNIQUE (UserID, LeagueID)
);

-- Create the MatchupRoster table
CREATE TABLE dbo.MatchupRoster (
    MatchupRosterID INT PRIMARY KEY,
    LeagueID VARCHAR(255),
    MatchupCode INT,
    RosterCode INT,
    Week INT,
    Points DECIMAL(18, 2)
);

-- Create the Player table
CREATE TABLE dbo.Player (
    PlayerID NVARCHAR(255) PRIMARY KEY,
    FirstName NVARCHAR(255),
    LastName NVARCHAR(255),
    Team NVARCHAR(255),
    Position NVARCHAR(255),
    InjuryStatus NVARCHAR(255),
    JSONData NVARCHAR(MAX)
);
-- Create the MatchupRosterPlayer table
CREATE TABLE dbo.MatchupRosterPlayer (
    MatchupRosterPlayerID INT PRIMARY KEY,
    MatchupRosterID INT,
    PlayerID NVARCHAR(255),
    Position NVARCHAR(255),
    Starter BIT,
    FOREIGN KEY (MatchupRosterID) REFERENCES dbo.MatchupRoster(MatchupRosterID),
    FOREIGN KEY (PlayerID) REFERENCES dbo.Player(PlayerID),
    CONSTRAINT unique_roster_player UNIQUE (MatchupRosterID, PlayerID)
);
