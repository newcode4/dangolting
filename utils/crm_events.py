"""랜딩 페이지 이벤트 수집 — 방문 · 참여 신청 클릭."""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVENTS_PATH = ROOT / "data" / "crm_events.jsonl"

ALLOWED_EVENTS = frozenset({"page_view", "apply_click", "faq_click"})


def _ensure_data_dir() -> None:
    EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)


def record_event(
    event: str,
    *,
    visitor_id: str = "",
    source: str = "landing",
) -> None:
    """이벤트 1건 append (JSONL)."""
    if event not in ALLOWED_EVENTS:
        return
    _ensure_data_dir()
    row = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "visitor_id": str(visitor_id or "").strip()[:64],
        "source": str(source or "landing").strip()[:32],
    }
    with EVENTS_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_events(*, limit: int | None = None) -> list[dict]:
    """저장된 이벤트 목록 (오래된 순)."""
    if not EVENTS_PATH.is_file():
        return []
    rows: list[dict] = []
    with EVENTS_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    if limit is not None and limit > 0:
        return rows[-limit:]
    return rows


def _event_date(iso_ts: str) -> date | None:
    try:
        return datetime.fromisoformat(str(iso_ts).replace("Z", "+00:00")).date()
    except (ValueError, TypeError):
        return None


def summarize_events(events: list[dict]) -> dict:
    """방문·클릭 집계 + 재방문 지표."""
    totals: dict[str, int] = {e: 0 for e in ALLOWED_EVENTS}
    uniques: dict[str, set[str]] = {e: set() for e in ALLOWED_EVENTS}
    by_day: dict[str, dict[str, int]] = {}

    for row in events:
        ev = str(row.get("event", "")).strip()
        if ev not in ALLOWED_EVENTS:
            continue
        totals[ev] += 1
        vid = str(row.get("visitor_id", "")).strip()
        if vid:
            uniques[ev].add(vid)
        day = _event_date(str(row.get("ts", "")))
        if day:
            key = day.isoformat()
            bucket = by_day.setdefault(key, {e: 0 for e in ALLOWED_EVENTS})
            bucket[ev] = bucket.get(ev, 0) + 1

    return {
        "totals": totals,
        "unique": {k: len(v) for k, v in uniques.items()},
        "by_day": dict(sorted(by_day.items())),
        "recent": list(reversed(events[-30:])),
        "visitors": visitor_metrics(events),
    }


def visitor_metrics(events: list[dict]) -> dict[str, int | float | None]:
    """재방문·유입 품질 (page_view 기준 visitor_id)."""
    pv_by_vid: dict[str, int] = {}
    days_by_vid: dict[str, set[date]] = {}

    for row in events:
        if str(row.get("event", "")).strip() != "page_view":
            continue
        vid = str(row.get("visitor_id", "")).strip()
        if not vid:
            continue
        pv_by_vid[vid] = pv_by_vid.get(vid, 0) + 1
        d = _event_date(str(row.get("ts", "")))
        if d:
            days_by_vid.setdefault(vid, set()).add(d)

    unique = len(pv_by_vid)
    total_pv = sum(pv_by_vid.values())
    if unique == 0:
        return {
            "unique_visitors": 0,
            "total_page_views": 0,
            "return_visitors": 0,
            "return_rate_pct": None,
            "multi_day_visitors": 0,
            "avg_views_per_visitor": 0.0,
        }

    return_visitors = sum(1 for c in pv_by_vid.values() if c >= 2)
    multi_day = sum(1 for days in days_by_vid.values() if len(days) >= 2)
    return {
        "unique_visitors": unique,
        "total_page_views": total_pv,
        "return_visitors": return_visitors,
        "return_rate_pct": round(return_visitors / unique * 100, 1),
        "multi_day_visitors": multi_day,
        "avg_views_per_visitor": round(total_pv / unique, 2),
    }


def demo_events() -> list[dict]:
    """데모 CRM용 샘플 이벤트."""
    today = date.today().isoformat()
    return [
        {"ts": f"{today}T09:12:00+00:00", "event": "page_view", "visitor_id": "demo_v1", "source": "landing"},
        {"ts": f"{today}T09:14:00+00:00", "event": "page_view", "visitor_id": "demo_v2", "source": "landing"},
        {"ts": f"{today}T09:15:00+00:00", "event": "apply_click", "visitor_id": "demo_v2", "source": "landing"},
        {"ts": f"{today}T10:02:00+00:00", "event": "page_view", "visitor_id": "demo_v3", "source": "landing"},
        {"ts": f"{today}T11:20:00+00:00", "event": "page_view", "visitor_id": "demo_v1", "source": "landing"},
        {"ts": f"{today}T11:21:00+00:00", "event": "apply_click", "visitor_id": "demo_v1", "source": "landing"},
        {"ts": f"{today}T14:00:00+00:00", "event": "page_view", "visitor_id": "demo_v4", "source": "landing"},
        {"ts": f"{today}T14:01:00+00:00", "event": "faq_click", "visitor_id": "demo_v4", "source": "landing"},
    ]
