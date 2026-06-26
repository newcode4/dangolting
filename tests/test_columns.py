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


def test_all_column_defaults_present():
    df = pd.DataFrame([{}])
    out = ensure_columns(df)
    for key in COLUMN_DEFAULTS:
        assert key in out.columns
