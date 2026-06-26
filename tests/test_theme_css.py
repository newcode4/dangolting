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
