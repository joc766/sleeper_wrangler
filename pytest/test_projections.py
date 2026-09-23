import json

import pytest
from sleeper_wrangler.sleeper_api import get_projections


@pytest.mark.integration
def test_get_projections():
    result = get_projections("2026", 1)
    with open(
        "/Users/jack/workspace/github.com/joc766/sleeper_wrangler/refs/temp.json", "w+"
    ) as f:
        json.dump(result, f)
