"""get_df 캐시 무효화."""
from __future__ import annotations

import pandas as pd

from utils.data_loader import expected_data_source, should_reload_df


def test_expected_data_source():
    assert expected_data_source(demo_mode=True, sheet_url="") == "demo"
    assert expected_data_source(demo_mode=False, sheet_url="http://x") == "sheet"
    assert expected_data_source(demo_mode=False, sheet_url="") == "none"


def test_should_reload_empty_demo_cache():
    empty = pd.DataFrame()
    assert should_reload_df(
        cached=empty,
        demo_mode=True,
        data_source="demo",
        expected_source="demo",
    )


def test_should_not_reload_valid_cache():
    df = pd.DataFrame({"name": ["a"]})
    assert not should_reload_df(
        cached=df,
        demo_mode=True,
        data_source="demo",
        expected_source="demo",
    )


def test_should_reload_on_mode_switch():
    df = pd.DataFrame({"name": ["a"]})
    assert should_reload_df(
        cached=df,
        demo_mode=False,
        data_source="demo",
        expected_source="sheet",
    )
