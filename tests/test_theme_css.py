"""theme.css 회귀 — 사이드바 토글 겹침."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "assets" / "theme.css"


def test_sidebar_toggle_not_fixed_overlap():
    text = THEME.read_text(encoding="utf-8")
    assert 'button[kind="headerNoPadding"]' not in text
    assert "position: fixed !important" not in text.split("collapsedControl")[0]
    idx = text.find("collapsedControl")
    if idx >= 0:
        chunk = text[idx : idx + 400]
        assert "position: fixed" not in chunk


def test_sidebar_force_open_when_collapsed():
    text = THEME.read_text(encoding="utf-8")
    assert '[aria-expanded="false"]' in text
    assert "margin-left: 0 !important" in text
    assert "width: 280px !important" in text


def test_admin_desktop_full_width_layout():
    text = THEME.read_text(encoding="utf-8")
    assert "max-width: none !important" in text
    assert "stAppViewBlockContainer" in text
    assert "body.dgt-admin" in text
    assert "dgt-admin-marker" in text
    assert "list-layout-anchor" in text
    assert "flex: 0 0 min(340px" in text
    assert "auth-page-marker" in text
    idx = text.find("/* ── 레이아웃 ── */")
    layout_chunk = text[idx : idx + 900]
    assert "flex: 0 0 260px" not in layout_chunk


def test_admin_theme_strips_landing_shell():
    import inspect

    from app import _inject_admin_theme, _strip_landing_shell_and_fix_admin_width

    theme_src = inspect.getsource(_inject_admin_theme)
    assert "dgt-admin-marker" in theme_src
    assert "_strip_landing_shell_and_fix_admin_width()" in theme_src
    shell_src = inspect.getsource(_strip_landing_shell_and_fix_admin_width)
    assert "dgt-landing-shell-css" in shell_src
    assert 'classList.remove("dgt-landing"' in shell_src
    assert "stAppViewBlockContainer" in shell_src


def test_admin_theme_injected_before_auth_gate():
    import inspect

    from app import _inject_admin_theme

    src = inspect.getsource(_inject_admin_theme)
    assert "_theme_css_inline()" in src
    app_src = open(THEME.parent.parent / "app.py", encoding="utf-8").read()
    gate_idx = app_src.find("_public_entry_gate(logo_data_uri())")
    inject_idx = app_src.find("if is_admin_route():")
    assert inject_idx > 0 and inject_idx < gate_idx
