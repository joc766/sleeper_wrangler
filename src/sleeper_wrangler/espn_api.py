import requests


def get_game_statuses() -> dict[str, float]:
    """
    Returns dictionary of team abbreviations as keys
    and float of percent complete as values
    """
    abbr_corrections = {"WSH": "WAS"}
    url = "https://site.api.espn.com/apis/fantasy/v2/games/ffl/games"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    completion_by_team: dict[str, float] = {}
    for event in data["events"]:
        for team in event["competitors"]:
            abbr = team["abbreviation"]
            if abbr in abbr_corrections:
                abbr = abbr_corrections[abbr]
            completion_by_team[abbr] = event["percentComplete"] / 100

    return completion_by_team
