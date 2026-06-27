"""시트 URL · 탭 이름 — 데모 전환 후에도 유지."""
from __future__ import annotations

import json
from pathlib import Path

from utils.columns import DEFAULT_SHEET_URL, DEFAULT_WORKSHEET

ROOT = Path(__file__).resolve().parent.parent
PREFS_FILE = ROOT / "data" / "sheet_prefs.json"


def load_sheet_prefs() -> tuple[str, str]:
    if not PREFS_FILE.is_file():
        return DEFAULT_SHEET_URL, DEFAULT_WORKSHEET
    try:
        data = json.loads(PREFS_FILE.read_text(encoding="utf-8"))
        url = str(data.get("sheet_url", "") or DEFAULT_SHEET_URL).strip()
        ws = str(data.get("ws_name", "") or DEFAULT_WORKSHEET).strip()
        return url or DEFAULT_SHEET_URL, ws or DEFAULT_WORKSHEET
    except (json.JSONDecodeError, OSError):
        return DEFAULT_SHEET_URL, DEFAULT_WORKSHEET


def save_sheet_prefs(sheet_url: str, ws_name: str) -> None:
    PREFS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PREFS_FILE.write_text(
        json.dumps(
            {"sheet_url": sheet_url.strip(), "ws_name": ws_name.strip()},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def active_sheet_config(*, demo_mode: bool, saved_url: str, saved_ws: str) -> tuple[str, str]:
    """데모면 로드 URL은 비우고, 저장값은 그대로 둠."""
    ws = (saved_ws or DEFAULT_WORKSHEET).strip() or DEFAULT_WORKSHEET
    if demo_mode:
        return "", ws
    url = (saved_url or DEFAULT_SHEET_URL).strip()
    return url, ws
