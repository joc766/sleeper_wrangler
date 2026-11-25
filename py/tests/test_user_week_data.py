import unittest

from sleeper_wrangler.losers.calc_loser_probs import Player, create_user_week_data


def starter(player_id, status):
    return Player(
        avatar=None,
        team_current_pts=5.0,
        player_id=player_id,
        team_abbr="CHI",
        position="RB",
        proj_pts=10.0,
        injury_status=status,
        curr_pts=5.0,
        proj_pts_no_tds=None,
        td_stats={},
    )


class InjuryMetadataTests(unittest.TestCase):
    def test_includes_injuries_without_changing_live_scores(self):
        players = [
            starter("out", " Out "),
            starter("questionable", "Questionable"),
            starter("healthy", "Healthy"),
            starter("empty", " "),
            starter("null", None),
        ]
        data = create_user_week_data({"manager": players}, {"CHI": 0.5})["manager"]
        self.assertEqual(
            data.injured_starters, {"out": "Out", "questionable": "Questionable"}
        )
        self.assertEqual(data.active_starters["out"], 5.0)

    def test_injuries_are_hidden_before_kickoff(self):
        data = create_user_week_data(
            {"manager": [starter("injured", "Doubtful")]}, {"CHI": 0.0}
        )["manager"]
        self.assertEqual(data.injured_starters, {})
        self.assertEqual(data.active_starters, {})
        self.assertEqual(data.yet_to_play, 1)

    def test_injuries_are_hidden_after_game_and_for_unknown_games(self):
        for completion in ({"CHI": 1.0}, {}):
            data = create_user_week_data(
                {"manager": [starter("injured", "Out")]}, completion
            )["manager"]
            self.assertEqual(data.injured_starters, {})

    def test_recovery_removes_injury(self):
        data = create_user_week_data(
            {"manager": [starter("recovered", None)]}, {"CHI": 0.5}
        )["manager"]
        self.assertEqual(data.injured_starters, {})


if __name__ == "__main__":
    unittest.main()
