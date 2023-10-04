import json
from pathlib import Path

import pytest

TEST_DIR = Path(__file__).parent
TEST_DATA_DIR = TEST_DIR / "data"


@pytest.fixture
def flux_jansky_dif():
    with open(TEST_DATA_DIR / "flux_jansky_dif.json") as f:
        return json.load(f)


@pytest.fixture
def lc_data(flux_jansky_dif):
    return {
        "light_curve": flux_jansky_dif,
        "ebv": 0.03,
        "name_model": "salt2",
        "t_min": 58250,
        "t_max": 58375,
        "count": 1000,
        "redshift": [0.01, 0.3],
    }
