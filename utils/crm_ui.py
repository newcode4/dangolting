"""CRM 대시보드 — 기간 필터 · 카테고리 탭 · 직관형 차트."""
from __future__ import annotations

import html as html_lib
from datetime import date, datetime, timedelta
import pandas as pd
import streamlit as st

from utils.crm import STAGE_LABELS, CrmSnapshot, build_crm_snapshot, crm_events_for_mode
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

    cols = st.columns(len(_PERIOD_OPTIONS))
    for col, label in zip(cols, _PERIOD_OPTIONS):
        with col:
            if st.button(
                label,
                key=f"crm_period_{label}",
                use_container_width=True,
                type="primary" if st.session_state["crm_period"] == label else "secondary",
            ):
                st.session_state["crm_period"] = label
                st.rerun()

    preset = st.session_state["crm_period"]
    d_start, d_end = _period_bounds(preset, data_min, data_max)
    st.caption(f"**{preset}** · {d_start.strftime('%Y.%m.%d')} ~ {d_end.strftime('%Y.%m.%d')}")
    return d_start, d_end, preset


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 처리 필요
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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
        st.success("✅ 처리 대기 없음")
        return
    cols = st.columns(len(active))
    for col, (n, title, desc, clr) in zip(cols, active):
        with col:
            st.markdown(
                f'<div style="background:{_C["bg"]};border:1px solid {_C["border"]};'
                f'border-left:3px solid {clr};border-radius:8px;padding:12px 14px">'
                f'<div style="font-size:1.4rem;font-weight:800;color:{clr}">{n}</div>'
                f'<div style="font-size:13px;font-weight:700;color:{_C["text"]}">{title}</div>'
                f'<div style="font-size:11px;color:{_C["muted"]};margin-top:2px">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


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
                conv = f'<div style="font-size:10px;color:{_C["refund"]};font-weight:700">제출 대비 {r}%</div>'
        elif i > 0 and counts[i - 1] > 0:
            r = round(cnt / counts[i - 1] * 100, 1)
            conv_clr = "#3fb950" if r >= 30 else "#d29922" if r >= 10 else "#f85149"
            conv = f'<div style="font-size:10px;color:{conv_clr};font-weight:700">{r}%</div>'
        parts.append(
            f'<div style="flex:1;text-align:center;min-width:0">'
            f'<div style="background:{_C["bg"]};border:1px solid {_C["border"]};'
            f'border-top:3px solid {clr};border-radius:8px;padding:10px 6px">'
            f'<div style="font-size:1.5rem;font-weight:900;color:{_C["text"]}">{cnt:,}</div>'
            f'<div style="font-size:11px;color:{_C["muted"]};font-weight:600">{label}</div>'
            f'{conv}'
            f'</div></div>'
        )
        if i < len(_KEY_FLOW) - 1:
            parts.append(
                f'<div style="flex:0 0 20px;display:flex;align-items:center;'
                f'justify-content:center;color:{_C["dim"]};font-size:16px;padding-bottom:14px">→</div>'
            )
    st.markdown(
        f'<div style="display:flex;align-items:stretch;gap:4px;margin:8px 0 16px">{"".join(parts)}</div>',
        unsafe_allow_html=True,
    )


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

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("순 방문자", f"{uv:,}명")
    c2.metric(
        "재방문",
        f"{ret:,}명",
        delta=f"{ret_pct}% 재방문율" if ret_pct is not None else None,
        delta_color="normal",
    )
    c3.metric("여러 날 방문", f"{multi:,}명", help="2일 이상 다른 날에 다시 온 방문자")
    c4.metric("평균 방문 횟수", f"{avg}회", help=f"총 페이지뷰 {total_pv:,}회")


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

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("환불", f"{refunded}명", delta=f"제출 대비 {period_biz.get('refund_rate_pct')}%" if refunded else None, delta_color="inverse")
    c2.metric("유지(환불 제외)", f"{active}명", delta=f"{ret_pct}% 유지율" if ret_pct is not None else None)
    c3.metric("매칭 완료", f"{matched}명", delta=f"입금 대비 {match_pct}%" if match_pct is not None else None)
    c4.metric("기간 순수익", f"{period_net:,}원", help=f"환불 {period_refund_amt:,}원 반영")

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
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("방문(순)", f"{pv:,}")
    c2.metric("신청 클릭", f"{ac:,}", delta=f"{round(ac/pv*100,1)}% 전환" if pv else None)
    c3.metric("폼 제출", f"{forms:,}", delta=f"{round(forms/ac*100,1)}% 전환" if ac else None)
    c4.metric("조회 기간", f"{days}일")


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
        height=300,
        margin=dict(l=8, r=8, t=32, b=8),
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
        st.markdown(
            f'<div style="font-size:12px;font-weight:700;color:{_C["muted"]};'
            f'margin:12px 0 8px;letter-spacing:0.04em">{group_title}</div>',
            unsafe_allow_html=True,
        )
        rows: list[str] = []
        for key in keys:
            step = step_map.get(key)
            if not step:
                continue
            w = max(4, int(step.count / max_count * 100))
            rate_txt = ""
            if step.rate_from_prev is not None:
                clr = "#3fb950" if step.rate_from_prev >= 30 else "#d29922" if step.rate_from_prev >= 10 else "#f85149"
                rate_txt = f'<span style="color:{clr};font-size:11px;font-weight:700;margin-left:8px">{step.rate_from_prev}%</span>'

            rows.append(
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">'
                f'<div style="width:110px;flex-shrink:0;font-size:12px;color:{_C["text"]};font-weight:600">'
                f'{html_lib.escape(step.label)}</div>'
                f'<div style="flex:1;height:22px;background:#21262d;border-radius:4px;overflow:hidden">'
                f'<div style="height:100%;width:{w}%;background:linear-gradient(90deg,#1f6feb,#58a6ff);border-radius:4px"></div>'
                f'</div>'
                f'<div style="width:60px;text-align:right;font-size:14px;font-weight:800;color:{_C["text"]}">{step.count}</div>'
                f'{rate_txt}'
                f'</div>'
            )
        st.markdown("".join(rows), unsafe_allow_html=True)


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
# 7. 신청자 테이블
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _render_applicant_table(snapshot: CrmSnapshot) -> None:
    if "crm_hidden_rows" not in st.session_state:
        st.session_state["crm_hidden_rows"] = set()
    hidden: set = st.session_state["crm_hidden_rows"]

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

    st.caption(
        f"표시 **{len(rows)}**명 · 입금 대기 **{snapshot.stage_counts.get('unpaid', 0)}** · "
        f"매칭 진행 **{snapshot.stage_counts.get('matching', 0)}**"
        + (f" · 숨김 **{len(hidden)}**" if hidden else "")
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 8. 데이터 관리
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _render_event_reset() -> None:
    with st.expander("⚙️ 데이터 관리", expanded=False):
        event_count = len(load_events())
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
def render_crm_tab(*, raw_df: pd.DataFrame, demo_mode: bool) -> None:
    events = crm_events_for_mode(demo_mode=demo_mode)
    snapshot = build_crm_snapshot(raw_df, events=events)

    # 데이터 범위
    all_days = sorted(
        set(snapshot.event_summary.get("by_day", {}).keys())
        | set(snapshot.daily_applicants.keys())
    )
    data_min = date.fromisoformat(all_days[0]) if all_days else None
    data_max = date.fromisoformat(all_days[-1]) if all_days else None

    # ── 헤더 ──
    st.markdown("#### CRM · 전환 퍼널")
    net = snapshot.revenue_paid - snapshot.revenue_refunded
    st.caption(
        f"참가비 {PARTICIPATION_FEE} · 입금 **{snapshot.revenue_paid:,}원** · "
        f"환불 **{snapshot.revenue_refunded:,}원** · 순수익 **{net:,}원**"
    )

    # ── 기간 선택 ──
    d_start, d_end, preset = _render_period_selector(data_min, data_max)
    period_events = _filter_events(events, d_start, d_end)
    period_ev = _period_event_totals(period_events)
    period_biz = _period_applicant_metrics(snapshot, d_start, d_end)
    period_visitors = visitor_metrics(period_events)
    period_days = (d_end - d_start).days + 1
    by_day = _period_by_day(period_events, d_start, d_end)

    # 기간별 폼 제출 일별
    daily_forms: dict[str, int] = {}
    for a in snapshot.applicants:
        d = parse_ts(a.get("신청일", ""))
        if d and d_start <= d <= d_end:
            key = d.isoformat()
            daily_forms[key] = daily_forms.get(key, 0) + 1

    st.markdown("---")

    # ── 카테고리 탭 ──
    tab_overview, tab_trend, tab_funnel, tab_people = st.tabs(
        ["👁 한눈에", "📈 추이", "🔽 퍼널·단계", "📋 신청자"]
    )

    with tab_overview:
        st.markdown("##### 🚨 지금 처리 필요")
        _render_action_alerts(snapshot)
        st.markdown("##### 전환 흐름")
        _render_conversion_flow(snapshot, period_ev, period_biz)
        _render_period_kpis(period_ev, period_biz, period_days)
        _render_traffic_quality(period_visitors)
        _render_outcome_metrics(period_biz, snapshot)

    with tab_trend:
        st.markdown("##### 일별 비교")
        st.caption("방문 · 클릭 · 제출을 날짜별로 나란히 비교합니다.")
        _render_trend_chart(by_day, daily_forms, d_start, d_end)
        _render_traffic_quality(period_visitors)
        _render_period_kpis(period_ev, period_biz, period_days)

    with tab_funnel:
        left, right = st.columns([3, 2], gap="large")
        with left:
            st.markdown("##### 퍼널 상세")
            _render_grouped_funnel(snapshot)
        with right:
            st.markdown("##### 단계 분포")
            _render_stage_bars(snapshot)

    with tab_people:
        _render_applicant_table(snapshot)

    st.markdown("---")
    _render_event_reset()
