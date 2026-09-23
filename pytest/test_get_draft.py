import pytest
from sleeper_wrangler.sleeper_api import get_draft


@pytest.mark.integration
def test_get_draft():
    league_id = "1384538107809902592"
    response = get_draft(league_id)
    print(response)
