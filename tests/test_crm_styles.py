"""CRM CSS 주입 — 회귀 테스트."""
import inspect

from utils.crm_styles import CRM_CSS_PATH, crm_css_inline, inject_crm_styles


def test_crm_css_file_exists():
    assert CRM_CSS_PATH.is_file()
    text = crm_css_inline()
    assert ".crm-bar-row" in text
    assert ".crm-queue-grid" in text


def test_inject_does_not_use_session_gate():
    src = inspect.getsource(inject_crm_styles)
    assert "_crm_styles_injected" not in src
    assert "dgt-crm-styles" in src
