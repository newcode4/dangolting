"""get_df 캐시 무효화 판단 — Streamlit 없이 테스트."""
from __future__ import annotations


def should_reload_df(
    *,
    cached,
    demo_mode: bool,
    data_source: str | None,
    expected_source: str,
) -> bool:
    """df 재로드 필요 여부."""
    if cached is None:
        return True
    if data_source != expected_source:
        return True
    if demo_mode and hasattr(cached, "empty") and cached.empty:
        return True
    return False


def expected_data_source(*, demo_mode: bool, sheet_url: str) -> str:
    if demo_mode:
        return "demo"
    if sheet_url:
        return "sheet"
    return "none"
