"""확장 폼 컬럼 로딩 · 프로필 전체 필드 표시."""
from __future__ import annotations

import pandas as pd

from utils.columns import LOGIC_KEYS, build_column_map, normalize_dataframe
from utils.profile_ui import _PROFILE_SECTIONS, profile_sections_html
from utils.sheets import records_from_sheet_values
from tests.test_columns_new_form import NEW_FORM_HEADERS, _row_kim


def _profile_field_keys() -> set[str]:
    keys: set[str] = set()
    for _title, _variant, fields in _PROFILE_SECTIONS:
        for key, _label in fields:
            keys.add(key)
    return keys


def test_new_form_extended_columns_mapped():
    m = build_column_map(NEW_FORM_HEADERS)
    for key in (
        "paid_self", "agree_refund", "agree_privacy", "refund_acct",
        "have_action", "have_where", "product", "pain_today",
        "worth_it", "portfolio", "buyer_intent",
    ):
        assert key in m, key
        assert key in LOGIC_KEYS, key


def test_new_form_extended_columns_loaded():
    row = _row_kim()
    row[20] = "AI 도입 컨설팅"
    row[21] = "사업계획서 PDF"
    row[22] = "B2B SaaS"
    row[23] = "첫 타겟 고객 선정"
    row[25] = "https://example.com/portfolio"
    all_values = [NEW_FORM_HEADERS, row]
    df = normalize_dataframe(pd.DataFrame(records_from_sheet_values(all_values)))
    assert df.loc[0, "have_action"] == "AI 도입 컨설팅"
    assert df.loc[0, "portfolio"] == "https://example.com/portfolio"


def test_profile_sections_include_all_logic_keys_except_matched_w():
    shown = _profile_field_keys()
    # matched_w는 시트 수식 열 — 프로필 관리 섹션에 표시
    assert "matched_w" in shown
    for key in (
        "ts", "job", "region", "years", "product",
        "w_job", "w_region", "w_gender", "w_years", "depth", "values",
        "want", "pain_today", "worth_it",
        "have", "have_action", "have_where",
        "note", "portfolio", "buyer_intent",
        "paid_self", "agree_refund", "agree_privacy", "refund_acct",
        "dday", "reject", "matched", "matched_at", "paid", "refund",
    ):
        assert key in shown, key


def test_profile_sections_render_extended_fields():
    row = {
        "ts": "2026. 7. 1",
        "name": "김현진",
        "have_action": "컨설팅 1시간",
        "portfolio": "https://example.com",
        "pain_today": "타겟 불명확",
    }

    def _dday(_):
        return "D-14"

    html = profile_sections_html(row, format_dday=_dday)
    assert "컨설팅 1시간" in html
    assert "https://example.com" in html
    assert "타겟 불명확" in html
    assert "관리 · 동의" in html
