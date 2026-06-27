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
    """실제 폼 시트: T=환불계좌, U=D-day, V=입금, W=횟수, X=매칭, Y=환불, Z=매칭일."""
    from utils.columns import COL

    assert COL["dday"] == 21
    assert COL["paid"] == 22
    assert COL["reject_count"] == 23
    assert COL["matched"] == 24
    assert COL["refund"] == 25
    assert COL["matched_at"] == 26


def test_build_column_map_trailing_admin_cols():
    from utils.columns import build_column_map

    headers = [
        "시간", "성함", "성별", "연락처", "직군", "지역",
        "", "", "", "", "", "", "", "", "", "", "", "", "",
        "환불 계좌", "남은 D-day", "입금확인", "매칭 횟수", "매칭 여부", "환불 여부", "매칭일",
    ]
    m = build_column_map(headers)
    assert m["paid"] == 21  # 0-based: V=22 -> index 21
    assert m["matched"] == 23  # X=24
    assert m["reject"] == 22  # W=23
    assert m["matched_at"] == 25  # Z=26


def test_all_column_defaults_present():
    df = pd.DataFrame([{}])
    out = ensure_columns(df)
    for key in COLUMN_DEFAULTS:
        assert key in out.columns
