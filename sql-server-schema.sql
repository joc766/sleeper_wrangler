

Table "dbo"."User" {
  "UserID" NVARCHAR(255) [pk]
  "UserName" NVARCHAR(255)
  "DisplayName" NVARCHAR(255)
  "JSONData" NVARCHAR(MAX)
}

Table "dbo"."League" {
  "LeagueID" NVARCHAR(255) [pk]
  "Season" NVARCHAR(255)
  "JSONData" NVARCHAR(MAX)
  "Previous_League_ID" NVARCHAR(255)
  "Name" NVARCHAR(255)
  "DraftID" NVARCHAR(255)
}

Table "dbo"."Team" {
  "TeamID" INT [pk]
  "RosterCode" INT
  "UserID" NVARCHAR(255)
  "LeagueID" NVARCHAR(255)
  "TeamName" NVARCHAR(255)
  "Record" NVARCHAR(255)
  "Streak" NVARCHAR(255)
  "Fpts" DECIMAL(18,2)
  "FptsAgainst" DECIMAL(18,2)
  "JSONData" NVARCHAR(MAX)

  Indexes {
    (UserID, LeagueID) [unique, name: "unique_owner"]
  }
}

Table "dbo"."MatchupRoster" {
  "MatchupRosterID" INT [pk]
  "LeagueID" VARCHAR(255)
  "MatchupCode" INT
  "RosterCode" INT
  "Week" INT
  "Points" DECIMAL(18,2)
}

Table "dbo"."Player" {
  "PlayerID" NVARCHAR(255) [pk]
  "FirstName" NVARCHAR(255)
  "LastName" NVARCHAR(255)
  "Team" NVARCHAR(255)
  "Position" NVARCHAR(255)
  "InjuryStatus" NVARCHAR(255)
  "JSONData" NVARCHAR(MAX)
}

Table "dbo"."MatchupRosterPlayer" {
  "MatchupRosterPlayerID" INT [pk]
  "MatchupRosterID" INT
  "PlayerID" NVARCHAR(255)
  "Position" NVARCHAR(255)
  "Starter" BIT

  Indexes {
    (MatchupRosterID, PlayerID) [unique, name: "unique_roster_player"]
  }
}

Ref:"dbo"."User"."UserID" < "dbo"."Team"."UserID"

Ref:"dbo"."League"."LeagueID" < "dbo"."Team"."LeagueID"

Ref:"dbo"."MatchupRoster"."MatchupRosterID" < "dbo"."MatchupRosterPlayer"."MatchupRosterID"

Ref:"dbo"."Player"."PlayerID" < "dbo"."MatchupRosterPlayer"."PlayerID"
