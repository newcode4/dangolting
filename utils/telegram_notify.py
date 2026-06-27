"""신규 신청자 → 텔레그램 Bot 알림"""
from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd
import streamlit as st

from utils.columns import cell, parse_checkbox
from utils.error_log import log_exception
from utils.sheets import load_data_raw
from utils.columns import DEFAULT_WORKSHEET

ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = ROOT / "data" / "telegram_notify_state.json"
TELEGRAM_FILE = ROOT / "data" / "telegram.toml"
NOTIFY_WS = "_알림"
DEFAULT_POLL_SECONDS = 120
_PLACEHOLDER_TOKEN = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
_PLACEHOLDER_CHAT = "123456789"


def _load_telegram_file() -> dict:
    """data/telegram.toml — secrets.toml 없을 때 로컬용."""
    if not TELEGRAM_FILE.is_file():
        return {}
    data: dict[str, str] = {}
    for line in TELEGRAM_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("["):
            continue
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        data[key] = val
    return data


def _tg_cfg() -> dict:
    cfg: dict = {}
    try:
        if "telegram" in st.secrets:
            cfg.update(dict(st.secrets["telegram"]))
    except Exception:
        pass

    cfg.update(_load_telegram_file())

    env_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    env_chat = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if env_token:
        cfg["bot_token"] = env_token
    if env_chat:
        cfg["chat_id"] = env_chat
    return cfg


def _is_real_value(token: str, chat_id: str) -> bool:
    if not token or not chat_id:
        return False
    if token == _PLACEHOLDER_TOKEN or chat_id == _PLACEHOLDER_CHAT:
        return False
    if "YOUR_" in token.upper() or "YOUR_" in chat_id.upper():
        return False
    return True


def telegram_enabled() -> bool:
    cfg = _tg_cfg()
    if cfg.get("enabled") is False:
        return False
    token = str(cfg.get("bot_token", "")).strip()
    chat_id = str(cfg.get("chat_id", "")).strip()
    return _is_real_value(token, chat_id)


def telegram_config_status() -> str:
    cfg = _tg_cfg()
    token = str(cfg.get("bot_token", "")).strip()
    chat_id = str(cfg.get("chat_id", "")).strip()
    if TELEGRAM_FILE.is_file() and _is_real_value(token, chat_id):
        return f"연동 준비됨 (data/telegram.toml)"
    try:
        if "telegram" in st.secrets and _is_real_value(token, chat_id):
            return "연동 준비됨 (secrets.toml)"
    except Exception:
        pass
    if token or chat_id:
        if not _is_real_value(token, chat_id):
            return "예시 값입니다 — 실제 bot_token · chat_id로 바꾸세요"
        return "연동 준비됨"
    if TELEGRAM_FILE.is_file():
        return "data/telegram.toml 값을 확인하세요"
    return "미설정 — data/telegram.toml 만들기 (아래 안내)"


def poll_interval_seconds() -> int:
    try:
        return max(60, int(_tg_cfg().get("poll_seconds", DEFAULT_POLL_SECONDS)))
    except (TypeError, ValueError):
        return DEFAULT_POLL_SECONDS


def _sheet_key(sheet_url: str, ws_name: str) -> str:
    raw = f"{sheet_url.strip()}|{ws_name.strip()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _load_local_state() -> dict:
    if not STATE_FILE.is_file():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_local_state(data: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_sheet_state(sheet_url: str, ws_name: str) -> int | None:
    try:
        from utils.sheets import _get_client

        client = _get_client()
        ss = client.open_by_url(sheet_url)
        try:
            meta = ss.worksheet(NOTIFY_WS)
        except Exception:
            meta = ss.add_worksheet(NOTIFY_WS, rows=10, cols=3)
            meta.update("A1:B1", [[ws_name.strip(), "0"]])
            return None
        rows = meta.get_all_values()
        target = ws_name.strip()
        for row in rows:
            if len(row) >= 2 and str(row[0]).strip() == target:
                val = row[1]
                return int(val) if val not in (None, "") else None
        # 구버전: A1에 숫자만 있으면 기본 워크시트 기준선으로 간주
        if rows and rows[0] and str(rows[0][0]).strip().isdigit():
            if target == DEFAULT_WORKSHEET or target == "시트1":
                return int(rows[0][0])
        return None
    except Exception:
        return None


def _save_sheet_state(sheet_url: str, ws_name: str, last_row: int) -> None:
    try:
        from utils.sheets import _get_client

        client = _get_client()
        ss = client.open_by_url(sheet_url)
        try:
            meta = ss.worksheet(NOTIFY_WS)
        except Exception:
            meta = ss.add_worksheet(NOTIFY_WS, rows=10, cols=3)
        rows = meta.get_all_values()
        target = ws_name.strip()
        for i, row in enumerate(rows, start=1):
            if row and str(row[0]).strip() == target:
                meta.update(f"B{i}", [[str(last_row)]])
                return
        # 구버전 단일 셀(A1 숫자) → 마이그레이션
        if rows and rows[0] and str(rows[0][0]).strip().isdigit():
            meta.update("A1:B1", [[target, str(last_row)]])
            return
        next_row = len(rows) + 1
        meta.update(f"A{next_row}:B{next_row}", [[target, str(last_row)]])
    except Exception:
        pass


def load_last_notified_row(sheet_url: str, ws_name: str) -> int | None:
    key = _sheet_key(sheet_url, ws_name)
    sheet_val = _load_sheet_state(sheet_url, ws_name)
    if sheet_val is not None:
        return sheet_val
    local = _load_local_state().get(key)
    return int(local) if local is not None else None


def save_last_notified_row(sheet_url: str, ws_name: str, last_row: int) -> None:
    key = _sheet_key(sheet_url, ws_name)
    data = _load_local_state()
    data[key] = last_row
    _save_local_state(data)
    _save_sheet_state(sheet_url, ws_name, last_row)


def send_telegram(text: str) -> bool:
    cfg = _tg_cfg()
    token = str(cfg.get("bot_token", "")).strip()
    chat_id = str(cfg.get("chat_id", "")).strip()
    if not _is_real_value(token, chat_id):
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    body = urllib.parse.urlencode(
        {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": "true",
        }
    ).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status == 200
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        log_exception(exc, where="telegram.send")
        return False


def _disp(val, default: str = "—") -> str:
    s = str(val if val is not None else "").strip()
    if not s or s.lower() in ("nan", "none"):
        return default
    return s


def format_applicant_message(row: pd.Series) -> str:
    name = _disp(cell(row, "name"))
    job = _disp(cell(row, "job"))
    if len(job) > 40:
        job = job[:37] + "…"
    region = _disp(cell(row, "region"))
    ts = _disp(cell(row, "ts"))
    contact = _disp(cell(row, "contact"))
    paid = parse_checkbox(cell(row, "paid", False))
    paid_txt = "✅ 입금 확인" if paid else "⏳ 입금 대기"

    return (
        "🆕 단골팅 새 신청\n"
        f"이름: {name}\n"
        f"연락: {contact}\n"
        f"직군: {job}\n"
        f"지역: {region}\n"
        f"신청: {ts}\n"
        f"{paid_txt}"
    )


def process_new_applicants(df: pd.DataFrame, sheet_url: str, ws_name: str) -> int:
    """신규 행 감지 후 텔레그램 발송. 발송 건수 반환."""
    if not telegram_enabled() or df.empty:
        return 0

    max_row = int(df.index.max())
    last = load_last_notified_row(sheet_url, ws_name)

    if last is None:
        save_last_notified_row(sheet_url, ws_name, max_row)
        return 0

    if max_row <= last:
        return 0

    new_rows = df[df.index > last].sort_index()
    sent = 0
    last_ok = last
    for idx, row in new_rows.iterrows():
        if send_telegram(format_applicant_message(row)):
            sent += 1
            last_ok = int(idx)
        else:
            break

    if last_ok > last:
        save_last_notified_row(sheet_url, ws_name, last_ok)

    return sent


def run_applicant_watch(sheet_url: str, ws_name: str) -> int:
    """시트 재조회 후 신규 신청 알림 (캐시 없음). 입금 대기도 알림 대상."""
    if not telegram_enabled() or not sheet_url:
        return 0
    try:
        df = load_data_raw(sheet_url, ws_name, apply_eligibility=False)
        return process_new_applicants(df, sheet_url, ws_name)
    except Exception as exc:
        log_exception(exc, where="telegram.watch")
        return 0


def send_test_notification() -> bool:
    return send_telegram("✅ 단골팅 알림 테스트\n텔레그램 연동이 정상입니다.")


def reset_notify_baseline(sheet_url: str, ws_name: str) -> None:
    """현재 시트 마지막 행을 기준선으로 — 이전 신청 알림 안 감."""
    try:
        df = load_data_raw(sheet_url, ws_name, apply_eligibility=False)
        last = int(df.index.max()) if not df.empty else 0
    except Exception:
        last = 0
    save_last_notified_row(sheet_url, ws_name, last)
