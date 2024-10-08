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


CREATE TABLE "League" (
  "LeagueID" TEXT PRIMARY KEY,
  "Season" TEXT,
  "JSONData" TEXT,
  "Previous_League_ID" TEXT,
  "Name" TEXT,
  "DraftID" INTEGER
);

CREATE TABLE "Team" (
  "TeamID" INTEGER PRIMARY KEY,
  "RosterCode" INTEGER,
  "UserID" TEXT,
  "LeagueID" TEXT,
  "TeamName" TEXT,
  "Record" TEXT,
  "Streak" TEXT,
  "Fpts" DECIMAL,
  "FptsAgainst" DECIMAL,
  "JSONData" TEXT,
  FOREIGN KEY ("UserID") REFERENCES "[User].UserID",
  FOREIGN KEY ("LeagueID") REFERENCES "League.LeagueID",
  CONSTRAINT unique_owner UNIQUE ("UserID", "LeagueID")
);

CREATE TABLE "MatchupRoster" (
  "MatchupRosterID" INTEGER PRIMARY KEY,
  "LeagueID" INTEGER,
  "MatchupCode" INTEGER,
  "RosterCode" INTEGER,
  "Week" INTEGER,
  "Points" DECIMAL
);

CREATE TABLE "MatchupRosterPlayer" (
  "MatchupRosterPlayerID" INTEGER PRIMARY KEY,
  "MatchupRosterID" INTEGER,
  "PlayerID" TEXT,
  "Position" TEXT,
  "Starter" bit,
  FOREIGN KEY ("MatchupRosterID") REFERENCES "MatchupRoster.MatchupRosterID",
  FOREIGN KEY ("PlayerID") REFERENCES "Player.PlayerID",
  CONSTRAINT unique_roster_player UNIQUE ("MatchupRosterID", "PlayerID")
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