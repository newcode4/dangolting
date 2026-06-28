"""CRM 대시보드 — 기간 필터 · 카테고리 탭 · 직관형 차트."""
from __future__ import annotations

import html as html_lib
from datetime import date, datetime, timedelta
import pandas as pd
import streamlit as st

from utils.crm import STAGE_LABELS, CrmSnapshot, build_crm_snapshot, crm_events_for_mode
from utils.crm_config import sla_unpaid_hours
from utils.crm_queue import QueueItem, build_today_queue
from utils.crm_styles import inject_crm_styles
from utils.crm_timeline import build_applicant_timeline
from utils.crm_truth import detect_sheet_anomalies, stage_labels_for_keys
from utils.crm_events import EVENTS_PATH, load_events, visitor_metrics
from utils.date_filter import parse_ts
from utils.landing_config import PARTICIPATION_FEE

# ── 색상 (theme.css와 통일) ──
_C = {
    "visit":  "#58a6ff",
    "click":  "#a371f7",
    "form":   "#3fb950",
    "paid":   "#39c5bb",
    "match":  "#d29922",
    "refund": "#f85149",
    "bg":     "#161b22",
    "border": "#30363d",
    "text":   "#e6edf3",
    "muted":  "#8b949e",
    "dim":    "#6e7681",
}

_STAGE_COLOR = {
    "unpaid":   "#d29922",
    "matching": "#58a6ff",
    "reject_1": "#a371f7",
    "matched":  "#3fb950",
    "closed":   "#f85149",
    "refunded": "#8b949e",
}

_PERIOD_OPTIONS = ("이번 주", "이번 달", "3개월", "전체")
_CRM_SUBTABS = ("한눈에", "추이", "퍼널", "신청자")


def _events_mtime() -> float:
    if not EVENTS_PATH.is_file():
        return 0.0
    return EVENTS_PATH.stat().st_mtime


def _get_cached_events(demo_mode: bool) -> list[dict]:
    if demo_mode:
        return crm_events_for_mode(demo_mode=True)
    mt = _events_mtime()
    key = ("ev", mt)
    if st.session_state.get("_crm_ev_key") == key and "_crm_ev" in st.session_state:
        return st.session_state["_crm_ev"]
    ev = load_events()
    st.session_state["_crm_ev_key"] = key
    st.session_state["_crm_ev"] = ev
    return ev


def _get_cached_snapshot(raw_df: pd.DataFrame, demo_mode: bool) -> tuple[CrmSnapshot, list[dict]]:
    events = _get_cached_events(demo_mode)
    load_ver = int(st.session_state.get("load_ver", 0))
    n = len(raw_df)
    max_row = int(raw_df.index.max()) if not raw_df.empty else 0
    key = (load_ver, demo_mode, n, max_row, st.session_state.get("_crm_ev_key"))
    if st.session_state.get("_crm_snap_key") == key and "_crm_snap" in st.session_state:
        return st.session_state["_crm_snap"], events
    snap = build_crm_snapshot(raw_df, events=events)
    st.session_state["_crm_snap_key"] = key
    st.session_state["_crm_snap"] = snap
    return snap, events


def _inject_crm_styles() -> None:
    inject_crm_styles()


def _fmt_step_rate(rate: float | None) -> str:
    """이전 단계 0일 때 200%+ 같은 misleading % 숨김."""
    if rate is None or rate < 0 or rate > 100:
        return ""
    clr = "#3fb950" if rate >= 30 else "#d29922" if rate >= 10 else "#f85149"
    return f'<span class="crm-bar-rate" style="color:{clr}">{rate}%</span>'


def _render_metric_grid(items: list[tuple[str, str, str | None, bool]]) -> None:
    """(label, value, delta, delta_warn) — st.metric 대신 모바일 안전 HTML."""
    cards = []
    for label, val, delta, warn in items:
        delta_html = ""
        if delta:
            cls = "crm-metric-delta crm-metric-delta--warn" if warn else "crm-metric-delta"
            delta_html = f'<div class="{cls}">{html_lib.escape(delta)}</div>'
        cards.append(
            f'<div class="crm-metric-card">'
            f'<div class="crm-metric-lbl">{html_lib.escape(label)}</div>'
            f'<div class="crm-metric-val">{html_lib.escape(val)}</div>'
            f"{delta_html}"
            f"</div>"
        )
    st.markdown(f'<div class="crm-metric-grid">{"".join(cards)}</div>', unsafe_allow_html=True)

# 퍼널 카테고리 — 핵심 단계만
_FUNNEL_GROUPS: list[tuple[str, list[str]]] = [
    ("📣 유입", ["visit_u", "apply_u"]),
    ("💰 전환", ["form", "paid", "unpaid"]),
    ("⚙️ 운영", ["matching_pool", "matched", "refunded"]),
]

_KEY_FLOW = [
    ("visit_u",  "방문",   _C["visit"]),
    ("apply_u",  "클릭",   _C["click"]),
    ("form",     "제출",   _C["form"]),
    ("paid",     "입금",   _C["paid"]),
    ("matched",  "매칭",   _C["match"]),
    ("refunded", "환불",   _C["refund"]),
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 기간 필터
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _period_bounds(preset: str, data_min: date | None, data_max: date | None) -> tuple[date, date]:
    today = date.today()
    end = data_max or today
    if preset == "이번 주":
        start = today - timedelta(days=today.weekday())
        return start, min(end, today)
    if preset == "이번 달":
        return today.replace(day=1), min(end, today)
    if preset == "3개월":
        return today - timedelta(days=89), min(end, today)
    # 전체
    start = data_min or (today - timedelta(days=29))
    return start, end


def _event_day(iso_ts: str) -> date | None:
    try:
        return datetime.fromisoformat(str(iso_ts).replace("Z", "+00:00")).date()
    except (ValueError, TypeError):
        return None


def _filter_events(events: list[dict], d_start: date, d_end: date) -> list[dict]:
    out = []
    for row in events:
        d = _event_day(str(row.get("ts", "")))
        if d and d_start <= d <= d_end:
            out.append(row)
    return out


def _period_event_totals(events: list[dict]) -> dict[str, int]:
    totals: dict[str, int] = {"page_view": 0, "apply_click": 0, "faq_click": 0}
    uniques: dict[str, set[str]] = {k: set() for k in totals}
    for row in events:
        ev = str(row.get("event", "")).strip()
        if ev not in totals:
            continue
        totals[ev] += 1
        vid = str(row.get("visitor_id", "")).strip()
        if vid:
            uniques[ev].add(vid)
    return {
        "pv_total": totals["page_view"],
        "pv_unique": len(uniques["page_view"]),
        "ac_total": totals["apply_click"],
        "ac_unique": len(uniques["apply_click"]),
    }


def _period_by_day(events: list[dict], d_start: date, d_end: date) -> dict[str, dict[str, int]]:
    days: dict[str, dict[str, int]] = {}
    cur = d_start
    while cur <= d_end:
        days[cur.isoformat()] = {"page_view": 0, "apply_click": 0}
        cur += timedelta(days=1)
    for row in events:
        d = _event_day(str(row.get("ts", "")))
        if not d:
            continue
        key = d.isoformat()
        if key not in days:
            continue
        ev = str(row.get("event", "")).strip()
        if ev in days[key]:
            days[key][ev] += 1
    return days


def _period_applicants(snapshot: CrmSnapshot, d_start: date, d_end: date) -> int:
    return _period_applicant_metrics(snapshot, d_start, d_end)["forms"]


def _period_applicant_metrics(snapshot: CrmSnapshot, d_start: date, d_end: date) -> dict[str, int | float | None]:
    forms = paid = matched = refunded = closed = 0
    for a in snapshot.applicants:
        d = parse_ts(a.get("신청일", ""))
        if not d or not (d_start <= d <= d_end):
            continue
        forms += 1
        if a.get("환불") == "✅":
            refunded += 1
        if a.get("입금") == "✅":
            paid += 1
        if a.get("매칭") == "✅":
            matched += 1
        if a.get("stage_key") == "closed" or a.get("단계") == STAGE_LABELS.get("closed"):
            closed += 1

    active = forms - refunded
    return {
        "forms": forms,
        "paid": paid,
        "matched": matched,
        "refunded": refunded,
        "closed": closed,
        "active": active,
        "refund_rate_pct": round(refunded / forms * 100, 1) if forms else None,
        "retention_pct": round(active / forms * 100, 1) if forms else None,
        "match_rate_pct": round(matched / paid * 100, 1) if paid else None,
    }


def _render_period_selector(data_min: date | None, data_max: date | None) -> tuple[date, date, str]:
    if "crm_period" not in st.session_state:
        st.session_state["crm_period"] = "이번 달"

    st.markdown(
        f'<div class="crm-toolbar">'
        f'<span class="crm-toolbar-range">'
        f'{html_lib.escape(st.session_state["crm_period"])} · '
        f'{_period_bounds(st.session_state["crm_period"], data_min, data_max)[0].strftime("%Y.%m.%d")} – '
        f'{_period_bounds(st.session_state["crm_period"], data_min, data_max)[1].strftime("%Y.%m.%d")}'
        f"</span></div>",
        unsafe_allow_html=True,
    )
    st.markdown('<div class="crm-period-wrap">', unsafe_allow_html=True)
    st.radio(
        "기간",
        _PERIOD_OPTIONS,
        horizontal=True,
        key="crm_period",
        label_visibility="collapsed",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    preset = str(st.session_state["crm_period"])
    d_start, d_end = _period_bounds(preset, data_min, data_max)
    return d_start, d_end, preset


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 처리 필요
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _section(title: str) -> None:
    st.markdown(f'<p class="crm-section-title">{html_lib.escape(title)}</p>', unsafe_allow_html=True)


def _apply_queue_filter(item: QueueItem) -> None:
    labels = stage_labels_for_keys(*item.stage_keys)
    st.session_state["crm_stage_filter"] = labels
    st.session_state["crm_queue_hint"] = f"「{item.title}」{item.count}명 · 신청자 탭에서 필터 적용됨"


def _render_anomaly_banner(raw_df: pd.DataFrame) -> None:
    anomalies = detect_sheet_anomalies(raw_df)
    if not anomalies:
        return
    st.markdown(
        f'<div class="crm-anomaly-banner">⚠ 시트 불일치 {len(anomalies)}건 — '
        f"입금·환불·매칭 상태를 확인하세요</div>",
        unsafe_allow_html=True,
    )
    with st.expander("불일치 행 보기", expanded=False):
        for a in anomalies[:20]:
            st.caption(f"행 {a.row_index + 2} · {a.name} · {a.message}")


def _render_today_queue(raw_df: pd.DataFrame) -> None:
    items = build_today_queue(raw_df, sla_hours=sla_unpaid_hours())
    _section("오늘 할 일")
    if not items:
        st.markdown(
            '<div class="crm-queue-empty">✅ 오늘 처리 대기 없음</div>',
            unsafe_allow_html=True,
        )
        return

    cards = []
    for item in items:
        urgent = " crm-queue-card--urgent" if item.urgent else ""
        sla = ""
        if item.sla_over:
            sla = f' · <span class="crm-queue-sla">{item.sla_over}명 SLA+</span>'
        cards.append(
            f'<div class="crm-queue-card{urgent}" style="--q-accent:{item.color}">'
            f'<div class="crm-queue-num" style="color:{item.color}">{item.count}</div>'
            f'<div class="crm-queue-body">'
            f'<div class="crm-queue-title">{html_lib.escape(item.title)}</div>'
            f'<div class="crm-queue-hint">{html_lib.escape(item.hint)}{sla}</div>'
            f"</div></div>"
        )
    st.markdown(f'<div class="crm-queue-block"><div class="crm-queue-grid">{"".join(cards)}</div></div>', unsafe_allow_html=True)

    n = len(items)
    cols = st.columns(min(n, 4))
    for i, item in enumerate(items):
        with cols[i % len(cols)]:
            label = item.title if item.count <= 99 else f"{item.title[:6]}…"
            if st.button(f"{label} ({item.count})", key=f"crm_queue_{item.key}", use_container_width=True):
                _apply_queue_filter(item)
                st.rerun()

    hint = st.session_state.pop("crm_queue_hint", None)
    if hint:
        st.caption(hint)


def _render_action_alerts(snapshot: CrmSnapshot) -> None:
    sc = snapshot.stage_counts
    items = [
        (sc.get("unpaid", 0),   "입금 대기",   "입금 확인 필요",     "#d29922"),
        (sc.get("reject_1", 0), "1차 거절",    "재매칭 확인",        "#a371f7"),
        (sc.get("matching", 0), "매칭 진행",   "연결 진행 중",       "#58a6ff"),
        (sc.get("refunded", 0), "환불",        "처리 완료",          "#8b949e"),
    ]
    active = [(n, t, d, c) for n, t, d, c in items if n > 0]
    if not active:
        st.caption("✅ 처리 대기 없음")
        return
    cards = []
    for n, title, desc, clr in active:
        cards.append(
            f'<div class="crm-alert-card" style="border-left-color:{clr}">'
            f'<div class="crm-alert-num" style="color:{clr}">{n}</div>'
            f'<div class="crm-alert-body">'
            f'<div class="crm-alert-title">{html_lib.escape(title)}</div>'
            f'<div class="crm-alert-desc">{html_lib.escape(desc)}</div>'
            f"</div></div>"
        )
    st.markdown(f'<div class="crm-alert-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. 5단계 전환 흐름 (한눈에)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _step_count(
    snapshot: CrmSnapshot,
    key: str,
    period_ev: dict[str, int],
    period_biz: dict[str, int | float | None],
) -> int:
    if key == "visit_u":
        return period_ev["pv_unique"]
    if key == "apply_u":
        return period_ev["ac_unique"]
    if key == "form":
        return int(period_biz["forms"])
    if key == "paid":
        return int(period_biz["paid"])
    if key == "matched":
        return int(period_biz["matched"])
    if key == "refunded":
        return int(period_biz["refunded"])
    step_map = {s.key: s.count for s in snapshot.funnel}
    return step_map.get(key, 0)


def _render_at_a_glance(
    period_ev: dict[str, int],
    period_biz: dict[str, int | float | None],
) -> None:
    """모바일·데스크톱 공통 — 핵심 4지표 한눈에."""
    items = [
        ("방문", period_ev["pv_unique"], _C["visit"]),
        ("클릭", period_ev["ac_unique"], _C["click"]),
        ("제출", int(period_biz.get("forms") or 0), _C["form"]),
        ("입금", int(period_biz.get("paid") or 0), _C["paid"]),
    ]
    cards = []
    for label, val, clr in items:
        cards.append(
            f'<div class="crm-glance-card" style="--accent:{clr}">'
            f'<div class="crm-glance-val">{val:,}</div>'
            f'<div class="crm-glance-lbl">{html_lib.escape(label)}</div>'
            f"</div>"
        )
    st.markdown(f'<div class="crm-glance-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def _render_conversion_flow(
    snapshot: CrmSnapshot,
    period_ev: dict[str, int],
    period_biz: dict[str, int | float | None],
) -> None:
    counts = [_step_count(snapshot, k, period_ev, period_biz) for k, _, _ in _KEY_FLOW]
    parts: list[str] = []
    for i, ((key, label, clr), cnt) in enumerate(zip(_KEY_FLOW, counts)):
        conv = ""
        if key == "refunded" and period_biz.get("forms"):
            r = period_biz["refund_rate_pct"]
            if r is not None:
                conv = f'<div class="crm-conv-rate crm-conv-rate--warn">제출 대비 {r}%</div>'
        elif i > 0 and counts[i - 1] > 0:
            r = round(cnt / counts[i - 1] * 100, 1)
            if 0 <= r <= 100:
                conv_cls = "crm-conv-rate--good" if r >= 30 else "crm-conv-rate--mid" if r >= 10 else "crm-conv-rate--bad"
                conv = f'<div class="crm-conv-rate {conv_cls}">{r}%</div>'
        parts.append(
            f'<div class="crm-conv-step" style="--step-color:{clr}">'
            f'<div class="crm-conv-count">{cnt:,}</div>'
            f'<div class="crm-conv-label">{html_lib.escape(label)}</div>'
            f"{conv}"
            f"</div>"
        )
        if i < len(_KEY_FLOW) - 1:
            parts.append('<div class="crm-conv-arrow" aria-hidden="true">→</div>')
    st.markdown(f'<div class="crm-conv-flow">{"".join(parts)}</div>', unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. 유입 품질 · 재방문
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _render_traffic_quality(visitors: dict[str, int | float | None]) -> None:
    st.markdown("##### 🔁 유입 품질 · 재방문")
    uv = int(visitors.get("unique_visitors") or 0)
    if uv == 0:
        st.caption("방문 데이터가 쌓이면 재방문 지표가 표시됩니다.")
        return

    ret = int(visitors.get("return_visitors") or 0)
    ret_pct = visitors.get("return_rate_pct")
    multi = int(visitors.get("multi_day_visitors") or 0)
    avg = visitors.get("avg_views_per_visitor") or 0
    total_pv = int(visitors.get("total_page_views") or 0)

    _render_metric_grid([
        ("순 방문자", f"{uv:,}명", None, False),
        ("재방문", f"{ret:,}명", f"{ret_pct}% 재방문율" if ret_pct is not None else None, False),
        ("여러 날 방문", f"{multi:,}명", "2일+ 재방문", False),
        ("평균 방문 횟수", f"{avg}회", f"PV {total_pv:,}회", False),
    ])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. 결과 · 환불
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _render_outcome_metrics(
    period_biz: dict[str, int | float | None],
    snapshot: CrmSnapshot,
) -> None:
    st.markdown("##### 💸 결과 · 환불")
    forms = int(period_biz.get("forms") or 0)
    if forms == 0:
        st.caption("선택 기간에 신청 데이터가 없습니다.")
        return

    refunded = int(period_biz.get("refunded") or 0)
    active = int(period_biz.get("active") or 0)
    matched = int(period_biz.get("matched") or 0)
    closed = int(period_biz.get("closed") or 0)
    ret_pct = period_biz.get("retention_pct")
    match_pct = period_biz.get("match_rate_pct")

    fee_digits = "".join(c for c in PARTICIPATION_FEE if c.isdigit())
    fee = int(fee_digits) if fee_digits else 0
    period_refund_amt = refunded * fee
    period_net = (int(period_biz.get("paid") or 0) - refunded) * fee

    _render_metric_grid([
        ("환불", f"{refunded}명", f"제출 대비 {period_biz.get('refund_rate_pct')}%" if refunded else None, True),
        ("유지(환불 제외)", f"{active}명", f"{ret_pct}% 유지율" if ret_pct is not None else None, False),
        ("매칭 완료", f"{matched}명", f"입금 대비 {match_pct}%" if match_pct is not None else None, False),
        ("기간 순수익", f"{period_net:,}원", f"환불 {period_refund_amt:,}원" if period_refund_amt else None, True),
    ])

    if closed:
        st.caption(f"종료(거절 2회) **{closed}**명 — 환불 없이 퍼널 종료")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. 기간 KPI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _render_period_kpis(
    period_ev: dict[str, int],
    period_biz: dict[str, int | float | None],
    days: int,
) -> None:
    pv = period_ev["pv_unique"]
    ac = period_ev["ac_unique"]
    forms = int(period_biz.get("forms") or 0)
    _render_metric_grid([
        ("방문(순)", f"{pv:,}", None, False),
        ("신청 클릭", f"{ac:,}", f"{round(ac/pv*100,1)}% 전환" if pv else None, False),
        ("폼 제출", f"{forms:,}", f"{round(forms/ac*100,1)}% 전환" if ac else None, False),
        ("조회 기간", f"{days}일", None, False),
    ])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. 추이 차트 — grouped bar (읽기 쉬움)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _fmt_day(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.month}/{d.day}"


def _render_trend_chart(
    by_day: dict[str, dict[str, int]],
    daily_forms: dict[str, int],
    d_start: date,
    d_end: date,
) -> None:
    try:
        import plotly.graph_objects as go
    except ImportError:
        st.caption("plotly 미설치")
        return

    days: list[str] = []
    cur = d_start
    while cur <= d_end:
        days.append(cur.isoformat())
        cur += timedelta(days=1)

    if not any(by_day.get(d, {}).get("page_view") or daily_forms.get(d, 0) for d in days):
        st.info("선택 기간에 데이터가 없습니다.")
        return

    labels = [_fmt_day(d) for d in days]
    pv  = [by_day.get(d, {}).get("page_view", 0) for d in days]
    ac  = [by_day.get(d, {}).get("apply_click", 0) for d in days]
    fm  = [daily_forms.get(d, 0) for d in days]

    fig = go.Figure()
    fig.add_trace(go.Bar(name="방문",  x=labels, y=pv, marker_color=_C["visit"],  marker_line_width=0))
    fig.add_trace(go.Bar(name="클릭",  x=labels, y=ac, marker_color=_C["click"],  marker_line_width=0))
    fig.add_trace(go.Bar(name="제출",  x=labels, y=fm, marker_color=_C["form"],   marker_line_width=0))

    fig.update_layout(
        barmode="group",
        bargap=0.25,
        bargroupgap=0.08,
        height=280,
        margin=dict(l=4, r=4, t=36, b=4),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=_C["muted"], size=12),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, x=0,
            bgcolor="rgba(0,0,0,0)", font=dict(color=_C["text"], size=12),
        ),
        xaxis=dict(
            type="category",
            showgrid=False,
            tickfont=dict(color=_C["muted"], size=11),
            linecolor=_C["border"],
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.06)",
            zeroline=False,
            tickfont=dict(color=_C["dim"], size=10),
        ),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. 퍼널 — 카테고리별 그룹
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _render_grouped_funnel(snapshot: CrmSnapshot) -> None:
    step_map = {s.key: s for s in snapshot.funnel}
    max_count = max((s.count for s in snapshot.funnel), default=1) or 1

    for group_title, keys in _FUNNEL_GROUPS:
        rows: list[str] = []
        for key in keys:
            step = step_map.get(key)
            if not step:
                continue
            w = max(4, int(step.count / max_count * 100))
            rate_txt = _fmt_step_rate(step.rate_from_prev)

            rows.append(
                f'<div class="crm-bar-row">'
                f'<div class="crm-bar-label">{html_lib.escape(step.label)}</div>'
                f'<div class="crm-bar-track">'
                f'<div class="crm-bar-fill" style="width:{w}%"></div>'
                f"</div>"
                f'<div class="crm-bar-cnt">{step.count}{rate_txt}</div>'
                f"</div>"
            )
        if not rows:
            continue
        st.markdown(
            f'<div class="crm-funnel-group">'
            f'<div class="crm-funnel-group-title">{group_title}</div>'
            f'{"".join(rows)}'
            f"</div>",
            unsafe_allow_html=True,
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. 단계 분포 — 가로 막대 (도넛 대신)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _render_stage_bars(snapshot: CrmSnapshot) -> None:
    try:
        import plotly.graph_objects as go
    except ImportError:
        return

    sc = snapshot.stage_counts
    keys = ["matching", "unpaid", "reject_1", "matched", "closed", "refunded"]
    labels = [STAGE_LABELS.get(k, k) for k in keys]
    values = [sc.get(k, 0) for k in keys]
    colors = [_STAGE_COLOR.get(k, "#64748b") for k in keys]

    # 0인 항목 제외
    filtered = [(l, v, c) for l, v, c in zip(labels, values, colors) if v > 0]
    if not filtered:
        st.caption("신청자 없음")
        return

    labels, values, colors = zip(*filtered)

    fig = go.Figure(go.Bar(
        x=list(values), y=list(labels), orientation="h",
        marker=dict(color=list(colors), line=dict(width=0)),
        text=[f"{v}명" for v in values],
        textposition="outside",
        textfont=dict(color=_C["text"], size=12),
        hovertemplate="<b>%{y}</b>: %{x}명<extra></extra>",
    ))
    fig.update_layout(
        height=max(160, len(labels) * 44),
        margin=dict(l=8, r=48, t=8, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", zeroline=False, showticklabels=False),
        yaxis=dict(tickfont=dict(color=_C["text"], size=12), autorange="reversed"),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. 신청자 테이블 + 타임라인
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _render_applicant_timeline(raw_df: pd.DataFrame, row_index: int, name: str) -> None:
    if raw_df.empty or row_index not in raw_df.index:
        return
    events = build_applicant_timeline(raw_df.loc[row_index])
    if not events:
        return
    items = []
    for ev in events:
        meta = html_lib.escape(ev.at)
        if ev.detail:
            meta = f"{meta} · {html_lib.escape(ev.detail)}" if meta != "—" else html_lib.escape(ev.detail)
        items.append(
            f'<li class="crm-timeline-item">'
            f'<span class="crm-timeline-dot"></span>'
            f'<div class="crm-timeline-body">'
            f'<div class="crm-timeline-label">{html_lib.escape(ev.label)}</div>'
            f'<div class="crm-timeline-meta">{meta}</div>'
            f"</div></li>"
        )
    st.markdown(
        f'<div class="crm-timeline">'
        f'<p class="crm-timeline-title">{html_lib.escape(name)} · 진행 이력</p>'
        f'<ul class="crm-timeline-list">{"".join(items)}</ul>'
        f"</div>",
        unsafe_allow_html=True,
    )


def _render_applicant_table(snapshot: CrmSnapshot, *, raw_df: pd.DataFrame) -> None:
    if "crm_hidden_rows" not in st.session_state:
        st.session_state["crm_hidden_rows"] = set()
    hidden: set = st.session_state["crm_hidden_rows"]

    st.markdown('<span class="crm-filter-anchor" aria-hidden="true"></span>', unsafe_allow_html=True)
    fa, fb, fc, fd = st.columns([3, 2, 1, 1])
    with fa:
        stage_filter = st.multiselect(
            "단계", options=list(STAGE_LABELS.values()),
            default=[], placeholder="전체 단계",
            key="crm_stage_filter", label_visibility="collapsed",
        )
    with fb:
        q = st.text_input("검색", placeholder="이름 · 연락처 · 직군",
                          key="crm_search", label_visibility="collapsed")
    with fc:
        show_hidden = st.checkbox("숨김 포함", key="crm_show_hidden")
    with fd:
        if hidden and st.button("숨김 해제", key="crm_unhide_all", use_container_width=True):
            st.session_state["crm_hidden_rows"] = set()
            st.rerun()

    rows = snapshot.applicants
    if not show_hidden:
        rows = [r for r in rows if r.get("행") not in hidden]
    if stage_filter:
        allowed = set(stage_filter)
        rows = [r for r in rows if r.get("단계") in allowed]
    if q.strip():
        needle = q.strip().lower()
        rows = [r for r in rows
                if needle in str(r.get("이름", "")).lower()
                or needle in str(r.get("연락처", "")).lower()
                or needle in str(r.get("직군", "")).lower()]

    if not rows:
        st.info("표시할 신청자가 없습니다.")
        return

    show_cols = ["신청일", "이름", "연락처", "단계", "입금", "매칭", "거절", "환불", "D-day", "직군", "지역", "행"]
    tbl = pd.DataFrame(rows)
    show_cols = [c for c in show_cols if c in tbl.columns]

    sel = st.dataframe(
        tbl[show_cols], use_container_width=True, hide_index=True,
        height=min(440, 44 + len(rows) * 36),
        on_select="rerun", selection_mode="multi-row",
    )
    sel_idx = sel.selection.get("rows", []) if hasattr(sel, "selection") else []
    if sel_idx:
        if st.button(f"🙈 {len(sel_idx)}명 숨기기", key="crm_hide_sel", type="secondary"):
            for i in sel_idx:
                rn = rows[i].get("행")
                if rn is not None:
                    hidden.add(rn)
            st.session_state["crm_hidden_rows"] = hidden
            st.rerun()
        first = rows[sel_idx[0]]
        row_i = first.get("행")
        if row_i is not None:
            _render_applicant_timeline(raw_df, int(row_i), str(first.get("이름", "")))

    st.caption(
        f"표시 **{len(rows)}**명 · 입금 대기 **{snapshot.stage_counts.get('unpaid', 0)}** · "
        f"매칭 진행 **{snapshot.stage_counts.get('matching', 0)}**"
        + (f" · 숨김 **{len(hidden)}**" if hidden else "")
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 8. 데이터 관리
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _render_event_reset(*, event_count: int) -> None:
    with st.expander("⚙️ 데이터 관리", expanded=False):
        st.caption(f"랜딩 이벤트 **{event_count}**건 · `{EVENTS_PATH.name}`")
        if "crm_reset_confirm" not in st.session_state:
            st.session_state["crm_reset_confirm"] = False
        if not st.session_state["crm_reset_confirm"]:
            if st.button("🗑 이벤트 기록 초기화", key="crm_reset_btn", type="secondary"):
                st.session_state["crm_reset_confirm"] = True
                st.rerun()
        else:
            st.warning("모든 방문·클릭 기록이 삭제됩니다.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ 확인", key="crm_reset_yes", type="primary"):
                    if EVENTS_PATH.is_file():
                        EVENTS_PATH.write_text("", encoding="utf-8")
                    st.session_state["crm_reset_confirm"] = False
                    st.success("초기화 완료!")
                    st.rerun()
            with c2:
                if st.button("취소", key="crm_reset_cancel"):
                    st.session_state["crm_reset_confirm"] = False
                    st.rerun()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@st.fragment
def _render_crm_period_and_body(
    *,
    raw_df: pd.DataFrame,
    snapshot: CrmSnapshot,
    events: list[dict],
    data_min: date | None,
    data_max: date | None,
) -> None:
    """기간·서브탭만 fragment — 이번 주/3개월 전환 시 전체 앱 rerun 방지."""
    d_start, d_end, _preset = _render_period_selector(data_min, data_max)

    period_events = _filter_events(events, d_start, d_end)
    period_ev = _period_event_totals(period_events)
    period_biz = _period_applicant_metrics(snapshot, d_start, d_end)
    period_visitors = visitor_metrics(period_events)
    period_days = (d_end - d_start).days + 1
    by_day = _period_by_day(period_events, d_start, d_end)

    daily_forms: dict[str, int] = {}
    for a in snapshot.applicants:
        d = parse_ts(a.get("신청일", ""))
        if d and d_start <= d <= d_end:
            key = d.isoformat()
            daily_forms[key] = daily_forms.get(key, 0) + 1

    sub = st.radio(
        "CRM 섹션",
        _CRM_SUBTABS,
        horizontal=True,
        key="crm_subtab",
        label_visibility="collapsed",
    )

    if sub == "한눈에":
        _section("핵심 지표")
        _render_at_a_glance(period_ev, period_biz)
        _section("단계별 현황")
        _render_action_alerts(snapshot)
        _section("전환 흐름")
        _render_conversion_flow(snapshot, period_ev, period_biz)
        with st.expander("상세 KPI · 유입 · 환불", expanded=False):
            _render_period_kpis(period_ev, period_biz, period_days)
            _render_traffic_quality(period_visitors)
            _render_outcome_metrics(period_biz, snapshot)
    elif sub == "추이":
        _section("일별 비교")
        st.caption("방문 · 클릭 · 제출 날짜별")
        _render_trend_chart(by_day, daily_forms, d_start, d_end)
        _render_traffic_quality(period_visitors)
        _render_period_kpis(period_ev, period_biz, period_days)
    elif sub == "퍼널":
        _section("퍼널 상세")
        _render_grouped_funnel(snapshot)
        _section("단계 분포")
        _render_stage_bars(snapshot)
    else:
        _render_applicant_table(snapshot, raw_df=raw_df)

    _render_event_reset(event_count=len(events))
    st.markdown("</div>", unsafe_allow_html=True)


def render_crm_tab(*, raw_df: pd.DataFrame, demo_mode: bool) -> None:
    _inject_crm_styles()
    st.markdown('<div class="crm-root">', unsafe_allow_html=True)
    snapshot, events = _get_cached_snapshot(raw_df, demo_mode)

    all_days = sorted(
        set(snapshot.event_summary.get("by_day", {}).keys())
        | set(snapshot.daily_applicants.keys())
    )
    data_min = date.fromisoformat(all_days[0]) if all_days else None
    data_max = date.fromisoformat(all_days[-1]) if all_days else None

    net = snapshot.revenue_paid - snapshot.revenue_refunded
    st.markdown(
        f'<div class="crm-head-bar">'
        f'<div class="crm-head-title">CRM · 전환 퍼널</div>'
        f'<div class="crm-head-revenue">'
        f"참가비 {html_lib.escape(PARTICIPATION_FEE)} · "
        f'입금 <b>{snapshot.revenue_paid:,}</b> · '
        f'환불 <b>{snapshot.revenue_refunded:,}</b> · '
        f"순수익 <b>{net:,}</b>원"
        f"</div></div>",
        unsafe_allow_html=True,
    )

    _render_today_queue(raw_df)
    _render_anomaly_banner(raw_df)
    _render_crm_period_and_body(
        raw_df=raw_df,
        snapshot=snapshot,
        events=events,
        data_min=data_min,
        data_max=data_max,
    )
