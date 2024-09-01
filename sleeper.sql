CREATE TABLE "User" (
  "UserID" TEXT,
  "UserName" TEXT,
  "DisplayName" TEXT,
  "JSONData" TEXT
);

CREATE TABLE "League" (
  "LeagueID" TEXT,
  "Season" varchar(4),
  "JSONData" TEXT,
  "Previous_League_ID" TEXT,
  "Name" TEXT,
  "DraftID" INTEGER
);

CREATE TABLE "LeagueUser" (
  "LeagueUserID" INTEGER,
  "UserID" TEXT,
  "LeagueID" TEXT,
  "TeamName" TEXT,
  "AvatarID" INTEGER
);

CREATE TABLE "Roster" (
  "RosterID" INTEGER,
  "OwnerID" TEXT,
  "Record" TEXT,
  "Streak" TEXT,
  "Fpts" int,
  "FptsAgainst" int,
  "JSONData" TEXT
);

CREATE TABLE "RosterPlayer" (
  "RosterPlayerID" INTEGER,
  "RosterID" INTEGER,
  "PlayerID" TEXT,
  "Position" TEXT,
  "Starter" bit
);

CREATE TABLE "Player" (
  "PlayerID" TEXT,
  "FirstName" TEXT,
  "LastName" TEXT,
  "Team" TEXT,
  "Position" TEXT,
  "InjuryStatus" TEXT,
  "JSONData" TEXT
);

CREATE TABLE "Matchup" (
  "MatchupID" INTEGER,
  "SleeperMatchupID" TEXT,
  "LeagueID" TEXT,
  "RosterID" TEXT,
  "Week" INTEGER
);

CREATE TABLE "MatchupRoster" (
  "MatchupRosterID" INTEGER,
  "MatchupID" INTEGER,
  "RosterID" INTEGER,
  "Points" INTEGER
);

CREATE TABLE "MatchupRosterPlayer" (
  "MatchupRosterID" INTEGER,
  "PlayerID" TEXT,
  "Starter" bit,
  "Points" bit
);

