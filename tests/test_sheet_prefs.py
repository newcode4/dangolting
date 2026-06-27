"""시트 설정 저장 — 데모 전환 후 유지."""
from __future__ import annotations

from utils.sheet_prefs import active_sheet_config, load_sheet_prefs, save_sheet_prefs


def test_active_sheet_config_demo_keeps_saved():
    url, ws = active_sheet_config(
        demo_mode=True,
        saved_url="https://docs.google.com/spreadsheets/d/abc/edit",
        saved_ws="시트1",
    )
    assert url == ""
    assert ws == "시트1"


def test_active_sheet_config_live_uses_saved():
    url, ws = active_sheet_config(
        demo_mode=False,
        saved_url="https://docs.google.com/spreadsheets/d/abc/edit",
        saved_ws="응답",
    )
    assert "abc" in url
    assert ws == "응답"


def test_save_and_load_sheet_prefs(tmp_path, monkeypatch):
    import utils.sheet_prefs as sp

    prefs = tmp_path / "sheet_prefs.json"
    monkeypatch.setattr(sp, "PREFS_FILE", prefs)
    save_sheet_prefs("https://example.com/sheet", "탭A")
    url, ws = load_sheet_prefs()
    assert url == "https://example.com/sheet"
    assert ws == "탭A"
