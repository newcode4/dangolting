"""시트 헤더 누락 시 KeyError 방지."""
from __future__ import annotations

import pandas as pd

from utils.columns import COLUMN_DEFAULTS, ensure_columns, normalize_dataframe


def test_ensure_columns_adds_matched():
    df = pd.DataFrame([{"성함": "홍길동"}])
    df.columns = [str(c).strip() for c in df.columns]
    out = ensure_columns(df)
    assert "matched" in out.columns
    assert out.loc[0, "matched"] == ""


def test_normalize_without_matched_header():
    row = {"시간": "2026. 1. 1", "성함": "테스트", "입금확인": True, "환불 여부": False}
    for key, header in [
        ("gender", "성별"), ("contact", "연락처"), ("job", "직군"),
        ("region", "지역"), ("years", "연차"), ("have", "제공가치"),
        ("reject", "매칭횟수"),
    ]:
        row[header] = ""
    df = pd.DataFrame([row])
    out = normalize_dataframe(df, apply_eligibility=False)
    assert "matched" in out.columns
    assert out["matched"].astype(str).str.upper().eq("TRUE").sum() == 0


def test_col_positions_form_layout():
    """확장 폼 시트: AC=D-day, AD=입금, AE=횟수, AF=매칭, AG=환불."""
    from utils.columns import COL

    assert COL["dday"] == 29
    assert COL["paid"] == 30
    assert COL["reject_count"] == 31
    assert COL["matched"] == 32
    assert COL["refund"] == 33
    assert COL["matched_at"] == 34


def test_build_column_map_trailing_admin_cols():
    from utils.columns import build_column_map

    from tests.test_columns_new_form import NEW_FORM_HEADERS

    m = build_column_map(NEW_FORM_HEADERS)
    assert m["paid"] == 29
    assert m["matched"] == 31
    assert m["reject"] == 30
    assert m["refund"] == 32


def test_all_column_defaults_present():
    df = pd.DataFrame([{}])
    out = ensure_columns(df)
    for key in COLUMN_DEFAULTS:
        assert key in out.columns
