"""데이터 로딩 성능 계약 — 이중 fetch 방지 · 캐시 키."""
import inspect

from utils import crm_ui, sheets, telegram_notify


def test_sheet_values_cached():
    src = inspect.getsource(sheets.load_data_raw)
    assert "_sheet_values_cached" in src
    assert "cache_version" in src


def test_demo_data_cached():
    assert hasattr(sheets, "load_demo_data_cached")


def test_telegram_watch_accepts_prefetched_df():
    sig = inspect.signature(telegram_notify.run_applicant_watch)
    assert "df" in sig.parameters
    assert "force_refresh" in sig.parameters


def test_crm_events_session_cache():
    assert "_get_cached_events" in inspect.getsource(crm_ui)
