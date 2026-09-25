import requests


def get_game_statuses() -> dict[str, float]:
    """
    Returns dictionary of team abbreviations as keys
    and float of percent complete as values.
    """
    abbr_corrections = {"WSH": "WAS"}
    url = "https://site.web.api.espn.com/apis/fantasy/v2/games/ffl/games"
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()
    completion_by_team: dict[str, float] = {}
    for event in data["events"]:
        for team in event["competitors"]:
            abbr = team["abbreviation"]
            if abbr in abbr_corrections:
                abbr = abbr_corrections[abbr]
            completion_by_team[abbr] = event["percentComplete"] / 100

    return completion_by_team


if __name__ == "__main__":
    print(get_game_statuses())
