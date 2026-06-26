"""데모 데이터 로드 — eligibility 필터로 0건 되지 않도록."""
from __future__ import annotations

from utils.sheets import load_demo_data


def test_load_demo_data_not_empty():
    df = load_demo_data()
    assert not df.empty
    assert len(df) >= 5
    assert "name" in df.columns
