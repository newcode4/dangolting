"""관리자 메인 탭 순서 · session_state 유지 계약."""
from pathlib import Path


def test_admin_tabs_matching_first_crm_last():
    src = Path(__file__).resolve().parents[1].joinpath("app.py").read_text(encoding="utf-8")
    assert '_ADMIN_TABS = ("매칭 작업"' in src
    assert '"CRM · 퍼널")' in src
    assert "st.tabs" not in src.split("_ADMIN_TABS")[1].split("if active_tab")[0]
    assert 'key="admin_tab"' in src
    assert '("admin_tab", "매칭 작업")' in src
