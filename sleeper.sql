DROP TABLE IF EXISTS "User";
DROP TABLE IF EXISTS "Player";
DROP TABLE IF EXISTS "League";
DROP TABLE IF EXISTS "LeagueUser";
DROP TABLE IF EXISTS "LeagueRoster";
DROP TABLE IF EXISTS "RosterPlayer";
DROP TABLE IF EXISTS "MatchupWeek";
DROP TABLE IF EXISTS "MatchupRoster";
DROP TABLE IF EXISTS "MatchupRosterPlayer";


CREATE TABLE "User" (
  "UserID" TEXT PRIMARY KEY,
  "UserName" TEXT,
  "DisplayName" TEXT,
  "JSONData" TEXT
);

CREATE TABLE "Player" (
  "PlayerID" TEXT PRIMARY KEY,
  "FirstName" TEXT,
  "LastName" TEXT,
  "Team" TEXT,
  "Position" TEXT,
  "InjuryStatus" TEXT,
  "JSONData" TEXT
);

CREATE TABLE "League" (
  "LeagueID" TEXT PRIMARY KEY,
  "Season" TEXT,
  "JSONData" TEXT,
  "Previous_League_ID" TEXT,
  "Name" TEXT,
  "DraftID" INTEGER
);

CREATE TABLE "LeagueUser" (
  "LeagueUserID" INTEGER PRIMARY KEY,
  "UserID" TEXT,
  "LeagueID" TEXT,
  "TeamName" TEXT,
  "AvatarID" INTEGER,
  FOREIGN KEY ("UserID") REFERENCES "[User].UserID",
  FOREIGN KEY ("LeagueID") REFERENCES "League.LeagueID"
);

CREATE TABLE "LeagueRoster" (
  "LeagueRosterID" INTEGER PRIMARY KEY,
  "RosterCode" INTEGER,
  "OwnerID" TEXT,
  "LeagueID" TEXT,
  "Record" TEXT,
  "Streak" TEXT,
  "Fpts" DECIMAL,
  "FptsAgainst" DECIMAL,
  "JSONData" TEXT,
  FOREIGN KEY ("OwnerID") REFERENCES "[User].UserID",
  FOREIGN KEY ("LeagueID") REFERENCES "League.LeagueID",
  CONSTRAINT unique_owner UNIQUE ("OwnerID", "LeagueID")
);

CREATE TABLE "RosterPlayer" (
  "RosterPlayerID" INTEGER PRIMARY KEY,
  "LeagueRosterID" INTEGER,
  "PlayerID" TEXT,
  "Position" TEXT,
  "Starter" bit,
  FOREIGN KEY ("LeagueRosterID") REFERENCES "LeagueRoster.LeagueRosterID",
  FOREIGN KEY ("PlayerID") REFERENCES "Player.PlayerID",
  CONSTRAINT unique_roster_player UNIQUE ("LeagueRosterID", "PlayerID")
);

CREATE TABLE "MatchupWeek" (
  "MatchupWeekID" INTEGER PRIMARY KEY,
  "MatchupCode" INTEGER,
  "Week" INTEGER,
  "LeagueID" TEXT,
  CONSTRAINT unique_matchup UNIQUE ("MatchupCode", "Week", "LeagueID")
);

CREATE TABLE "MatchupRoster" (
  "MatchupRosterID" INTEGER PRIMARY KEY,
  "MatchupWeekID" INTEGER,
  "OwnerRosterCode" INTEGER,
  "Points" DECIMAL,
  FOREIGN KEY ("MatchupWeekID") REFERENCES "MatchupWeek.MatchupWeekID",
  CONSTRAINT unique_owner UNIQUE ("MatchupWeekID", "OwnerRosterCode")
);

CREATE TABLE "MatchupRosterPlayer" (
  "MatchupRosterPlayerID" INTEGER PRIMARY KEY,
  "MatchupRosterID" INTEGER,
  "PlayerID" TEXT,
  "Starter" BIT,
  "Points" DECIMAL,
  FOREIGN KEY ("MatchupRosterID") REFERENCES "MatchupRoster.MatchupRosterID"
);
