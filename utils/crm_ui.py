"""CRM 대시보드 UI."""
from __future__ import annotations

import html as html_lib
from typing import Any

import pandas as pd
import streamlit as st

from utils.crm import STAGE_LABELS, CrmSnapshot, build_crm_snapshot, crm_events_for_mode
from utils.crm_events import EVENTS_PATH
from utils.landing_config import PARTICIPATION_FEE


def _rate_label(rate: float | None) -> str:
    if rate is None:
        return "—"
    return f"{rate}%"


def _render_funnel(snapshot: CrmSnapshot) -> None:
    max_count = max((s.count for s in snapshot.funnel), default=1) or 1
    bars = []
    for step in snapshot.funnel:
        width = max(4, int(step.count / max_count * 100))
        prev = _rate_label(step.rate_from_prev)
        top = _rate_label(step.rate_from_top)
        sub = []
        if step.unique is not None and step.unique != step.count:
            sub.append(f"순 {step.unique}")
        if step.rate_from_prev is not None:
            sub.append(f"이전 대비 {prev}")
        if step.rate_from_top is not None:
            sub.append(f"방문 대비 {top}")
        meta = " · ".join(sub) if sub else step.hint
        bars.append(
            f'<div class="crm-funnel-row">'
            f'<div class="crm-funnel-meta">'
            f'<span class="crm-funnel-label">{html_lib.escape(step.label)}</span>'
            f'<span class="crm-funnel-count"><b>{step.count:,}</b></span>'
            f'</div>'
            f'<div class="crm-funnel-track"><div class="crm-funnel-fill" style="width:{width}%"></div></div>'
            f'<div class="crm-funnel-hint">{html_lib.escape(meta or step.hint)}</div>'
            f'</div>'
        )
    st.markdown(f'<div class="crm-funnel">{"".join(bars)}</div>', unsafe_allow_html=True)


def _render_kpis(snapshot: CrmSnapshot) -> None:
    sc = snapshot.stage_counts
    cards = [
        ("방문(순)", snapshot.event_summary.get("unique", {}).get("page_view", 0), "crm-kpi-blue"),
        ("신청 클릭", snapshot.event_summary.get("unique", {}).get("apply_click", 0), "crm-kpi-indigo"),
        ("폼 제출", snapshot.form_total, "crm-kpi-violet"),
        ("입금", sc.get("matching", 0) + sc.get("reject_1", 0) + sc.get("matched", 0) + sc.get("closed", 0), "crm-kpi-green"),
        ("매칭", sc.get("matched", 0), "crm-kpi-teal"),
        ("환불", sc.get("refunded", 0), "crm-kpi-rose"),
    ]
    html = '<div class="crm-kpi-grid">'
    for label, val, cls in cards:
        html += (
            f'<div class="crm-kpi {cls}">'
            f'<div class="crm-kpi-val">{val:,}</div>'
            f'<div class="crm-kpi-lbl">{html_lib.escape(label)}</div>'
            f'</div>'
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def _render_stage_chips(snapshot: CrmSnapshot) -> None:
    chips = []
    for key in ("unpaid", "matching", "reject_1", "matched", "closed", "refunded"):
        n = snapshot.stage_counts.get(key, 0)
        chips.append(
            f'<span class="crm-stage-chip crm-stage-{key}">'
            f'{html_lib.escape(STAGE_LABELS[key])} <b>{n}</b></span>'
        )
    st.markdown(f'<div class="crm-stage-bar">{"".join(chips)}</div>', unsafe_allow_html=True)


def render_crm_tab(*, raw_df: pd.DataFrame, demo_mode: bool) -> None:
    events = crm_events_for_mode(demo_mode=demo_mode)
    snapshot = build_crm_snapshot(raw_df, events=events)

    st.markdown("#### CRM · 전환 퍼널")
    st.caption(
        "랜딩 **방문·신청 클릭**은 자동 수집 · **폼·입금·매칭·환불**은 구글 시트 기준. "
        f"참가비 {PARTICIPATION_FEE} · 입금 {snapshot.revenue_paid:,}원 · 환불 {snapshot.revenue_refunded:,}원"
    )

    _render_kpis(snapshot)
    st.markdown('<div class="crm-section-gap"></div>', unsafe_allow_html=True)
    _render_stage_chips(snapshot)

    left, right = st.columns([11, 9], gap="large")
    with left:
        st.markdown("##### 퍼널 상세")
        _render_funnel(snapshot)

    with right:
        st.markdown("##### 일별 추이")
        if snapshot.event_summary.get("by_day") or snapshot.daily_applicants:
            days = sorted(set(snapshot.event_summary.get("by_day", {}).keys()) | set(snapshot.daily_applicants.keys()))
            chart_rows = []
            for d in days[-14:]:
                ev = snapshot.event_summary.get("by_day", {}).get(d, {})
                chart_rows.append(
                    {
                        "날짜": d,
                        "방문": ev.get("page_view", 0),
                        "신청클릭": ev.get("apply_click", 0),
                        "폼제출": snapshot.daily_applicants.get(d, 0),
                    }
                )
            if chart_rows:
                st.line_chart(pd.DataFrame(chart_rows).set_index("날짜"), height=220)
            else:
                st.caption("아직 일별 데이터가 없습니다.")
        else:
            st.caption("이벤트·신청 데이터가 쌓이면 차트가 표시됩니다.")

        with st.expander("최근 랜딩 이벤트", expanded=False):
            recent: list[dict[str, Any]] = snapshot.event_summary.get("recent", [])
            if not recent:
                st.caption("수집된 이벤트 없음 — 랜딩 페이지 방문 후 표시됩니다.")
            else:
                for row in recent[:15]:
                    st.text(
                        f"{str(row.get('ts', ''))[:19]}  "
                        f"{row.get('event', '—')}  "
                        f"vid={row.get('visitor_id', '—')[:12]}"
                    )
            st.caption(f"저장: `{EVENTS_PATH.name}` (git 제외)")

    st.divider()
    st.markdown("##### 신청자 파이프라인")

    stage_filter = st.multiselect(
        "단계 필터",
        options=list(STAGE_LABELS.values()),
        default=[],
        placeholder="전체 단계",
        key="crm_stage_filter",
    )
    q = st.text_input(
        "검색",
        placeholder="이름 · 연락처 · 직군",
        label_visibility="collapsed",
        key="crm_search",
    )

    rows = snapshot.applicants
    if stage_filter:
        allowed = set(stage_filter)
        rows = [r for r in rows if r.get("단계") in allowed]
    if q.strip():
        needle = q.strip().lower()
        rows = [
            r
            for r in rows
            if needle in str(r.get("이름", "")).lower()
            or needle in str(r.get("연락처", "")).lower()
            or needle in str(r.get("직군", "")).lower()
        ]

    if not rows:
        st.info("표시할 신청자가 없습니다.")
        return

    table = pd.DataFrame(rows)
    show_cols = ["신청일", "이름", "연락처", "단계", "입금", "매칭", "거절", "환불", "D-day", "매칭일", "직군", "지역", "행"]
    show_cols = [c for c in show_cols if c in table.columns]
    st.dataframe(
        table[show_cols],
        use_container_width=True,
        hide_index=True,
        height=min(420, 44 + len(rows) * 36),
    )
    st.caption(f"총 **{len(rows)}**명 · 입금 대기 **{snapshot.stage_counts.get('unpaid', 0)}** · 매칭 진행 **{snapshot.stage_counts.get('matching', 0)}**")
