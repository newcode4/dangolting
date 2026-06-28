"""CRM UI 계약 — DOM 마커 · 탭 · CSS."""
import inspect
from pathlib import Path

from utils import crm_ui


def test_crm_tab_order():
    src = inspect.getsource(crm_ui._render_crm_period_and_body)
    assert "_CRM_SUBTABS" in src
    assert "한눈에" in crm_ui._CRM_SUBTABS and "신청자" in crm_ui._CRM_SUBTABS


def test_crm_lazy_subtabs_no_st_tabs():
    src = inspect.getsource(crm_ui._render_crm_period_and_body)
    assert "st.tabs" not in src
    assert "crm_subtab" in src


def test_crm_period_fragment():
    src = inspect.getsource(crm_ui._render_crm_period_and_body)
    assert "@st.fragment" in inspect.getsource(crm_ui) or "fragment" in src


def test_crm_snapshot_cache():
    assert "_get_cached_snapshot" in inspect.getsource(crm_ui.render_crm_tab)


def test_crm_today_queue_markers():
    css = Path(__file__).resolve().parents[1].joinpath("assets", "crm.css").read_text(encoding="utf-8")
    src = inspect.getsource(crm_ui._render_today_queue)
    main = inspect.getsource(crm_ui.render_crm_tab)
    assert "crm-queue-grid" in css
    assert "crm-queue-empty" in css
    assert "오늘 할 일" in src
    assert "_render_today_queue" in main
    assert "crm-root" in main


def test_crm_styles_module_injected():
    src = inspect.getsource(crm_ui._inject_crm_styles)
    assert "inject_crm_styles()" in src


def test_crm_timeline_in_people_tab():
    src = inspect.getsource(crm_ui._render_applicant_table)
    assert "_render_applicant_timeline" in src


def test_fmt_step_rate_caps_misleading():
    assert crm_ui._fmt_step_rate(233.3) == ""
    assert "30.0%" in crm_ui._fmt_step_rate(30.0)
