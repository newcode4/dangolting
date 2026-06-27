"""CRM 대시보드 UI."""
from __future__ import annotations

import html as html_lib
from typing import Any

import pandas as pd
import streamlit as st

from utils.crm import STAGE_LABELS, CrmSnapshot, build_crm_snapshot, crm_events_for_mode
from utils.crm_events import EVENTS_PATH, load_events
from utils.landing_config import PARTICIPATION_FEE

# ── 단계 색상 ──
_STAGE_COLOR = {
    "unpaid": "#f59e0b",
    "matching": "#6366f1",
    "reject_1": "#ef4444",
    "matched": "#10b981",
    "closed": "#64748b",
    "refunded": "#ec4899",
}


def _rate_label(rate: float | None) -> str:
    if rate is None:
        return "—"
    return f"{rate}%"


def _pct_color(rate: float | None) -> str:
    if rate is None:
        return "#64748b"
    if rate >= 50:
        return "#10b981"
    if rate >= 20:
        return "#f59e0b"
    return "#ef4444"


# ── 전환율 요약 바 ──────────────────────────────────────────────
def _render_conversion_summary(snapshot: CrmSnapshot) -> None:
    ev = snapshot.event_summary.get("unique", {})
    pv = ev.get("page_view", 0)
    ac = ev.get("apply_click", 0)
    fm = snapshot.form_total

    sc = snapshot.stage_counts
    paid_total = (
        sc.get("matching", 0) + sc.get("reject_1", 0)
        + sc.get("matched", 0) + sc.get("closed", 0)
    )
    matched = sc.get("matched", 0)

    def pct(n: int, d: int) -> float | None:
        return round(n / d * 100, 1) if d else None

    steps = [
        ("방문", pv, None, "👁"),
        ("신청클릭", ac, pct(ac, pv), "🖱️"),
        ("폼제출", fm, pct(fm, ac), "📝"),
        ("입금", paid_total, pct(paid_total, fm), "💳"),
        ("매칭완료", matched, pct(matched, paid_total), "🤝"),
    ]

    parts = []
    for label, cnt, rate, icon in steps:
        color = _pct_color(rate)
        rate_html = (
            f'<span style="font-size:11px;color:{color};font-weight:700;">'
            f'↑ {rate}%</span>' if rate is not None else ""
        )
        parts.append(
            f'<div class="crm-conv-step">'
            f'<div class="crm-conv-icon">{icon}</div>'
            f'<div class="crm-conv-count">{cnt:,}</div>'
            f'<div class="crm-conv-label">{label}</div>'
            f'{rate_html}'
            f'</div>'
        )
        if label != "매칭완료":
            parts.append('<div class="crm-conv-arrow">→</div>')

    html = f'<div class="crm-conv-bar">{"".join(parts)}</div>'
    st.markdown(html, unsafe_allow_html=True)


# ── KPI 카드 ──────────────────────────────────────────────────
def _render_kpis(snapshot: CrmSnapshot) -> None:
    ev = snapshot.event_summary.get("unique", {})
    sc = snapshot.stage_counts
    paid_total = (
        sc.get("matching", 0) + sc.get("reject_1", 0)
        + sc.get("matched", 0) + sc.get("closed", 0)
    )
    cards = [
        ("방문(순)", ev.get("page_view", 0), "crm-kpi-blue", "고유 방문자 수"),
        ("신청클릭", ev.get("apply_click", 0), "crm-kpi-indigo", "CTA 클릭"),
        ("폼제출", snapshot.form_total, "crm-kpi-violet", "구글 시트 신청"),
        ("입금확인", paid_total, "crm-kpi-green", "참가비 납부"),
        ("매칭완료", sc.get("matched", 0), "crm-kpi-teal", "1:1 연결됨"),
        ("환불", sc.get("refunded", 0), "crm-kpi-rose", "참가비 환불"),
    ]
    html = '<div class="crm-kpi-grid">'
    for label, val, cls, hint in cards:
        html += (
            f'<div class="crm-kpi {cls}" title="{hint}">'
            f'<div class="crm-kpi-val">{val:,}</div>'
            f'<div class="crm-kpi-lbl">{html_lib.escape(label)}</div>'
            f'<div class="crm-kpi-hint">{hint}</div>'
            f'</div>'
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ── 단계 칩 ──────────────────────────────────────────────────
def _render_stage_chips(snapshot: CrmSnapshot) -> None:
    chips = []
    for key in ("unpaid", "matching", "reject_1", "matched", "closed", "refunded"):
        n = snapshot.stage_counts.get(key, 0)
        color = _STAGE_COLOR.get(key, "#64748b")
        chips.append(
            f'<span class="crm-stage-chip crm-stage-{key}">'
            f'{html_lib.escape(STAGE_LABELS[key])} '
            f'<b style="color:{color}">{n}</b></span>'
        )
    st.markdown(f'<div class="crm-stage-bar">{"".join(chips)}</div>', unsafe_allow_html=True)


# ── 퍼널 바 차트 ──────────────────────────────────────────────
def _render_funnel(snapshot: CrmSnapshot) -> None:
    max_count = max((s.count for s in snapshot.funnel), default=1) or 1
    bars = []
    for step in snapshot.funnel:
        width = max(4, int(step.count / max_count * 100))
        prev = _rate_label(step.rate_from_prev)
        top = _rate_label(step.rate_from_top)

        badges = []
        if step.rate_from_prev is not None:
            color = _pct_color(step.rate_from_prev)
            badges.append(
                f'<span class="crm-rate-badge" style="color:{color}">이전대비 {prev}</span>'
            )
        if step.rate_from_top is not None:
            badges.append(
                f'<span class="crm-rate-badge crm-rate-dim">방문대비 {top}</span>'
            )

        badge_html = "".join(badges)
        bars.append(
            f'<div class="crm-funnel-row">'
            f'<div class="crm-funnel-meta">'
            f'<span class="crm-funnel-label">{html_lib.escape(step.label)}</span>'
            f'<div class="crm-funnel-badges">{badge_html}</div>'
            f'</div>'
            f'<div class="crm-funnel-track">'
            f'<div class="crm-funnel-fill" style="width:{width}%"></div>'
            f'<span class="crm-funnel-cnt">{step.count:,}</span>'
            f'</div>'
            f'</div>'
        )
    st.markdown(f'<div class="crm-funnel">{"".join(bars)}</div>', unsafe_allow_html=True)


# ── 단계 분포 바 차트 ─────────────────────────────────────────
def _render_stage_bar(snapshot: CrmSnapshot) -> None:
    sc = snapshot.stage_counts
    data = {
        STAGE_LABELS.get(k, k): sc.get(k, 0)
        for k in ("unpaid", "matching", "reject_1", "matched", "closed", "refunded")
    }
    df = pd.DataFrame.from_dict({"인원": data}, orient="columns")
    st.bar_chart(df, height=200, color="#3b82f6")


# ── 신청자 테이블 (soft delete) ───────────────────────────────
def _render_applicant_table(
    snapshot: CrmSnapshot,
    raw_df: pd.DataFrame,
) -> None:
    st.markdown("##### 신청자 파이프라인")

    if "crm_hidden_rows" not in st.session_state:
        st.session_state["crm_hidden_rows"] = set()
    hidden: set = st.session_state["crm_hidden_rows"]

    fa, fb, fc = st.columns([3, 2, 1])
    with fa:
        stage_filter = st.multiselect(
            "단계 필터",
            options=list(STAGE_LABELS.values()),
            default=[],
            placeholder="전체 단계",
            key="crm_stage_filter",
            label_visibility="collapsed",
        )
    with fb:
        q = st.text_input(
            "검색",
            placeholder="이름 · 연락처 · 직군",
            key="crm_search",
            label_visibility="collapsed",
        )
    with fc:
        show_hidden = st.checkbox("숨긴 항목 포함", key="crm_show_hidden")

    rows = snapshot.applicants
    if not show_hidden:
        rows = [r for r in rows if r.get("행") not in hidden]
    if stage_filter:
        allowed = set(stage_filter)
        rows = [r for r in rows if r.get("단계") in allowed]
    if q.strip():
        needle = q.strip().lower()
        rows = [
            r for r in rows
            if needle in str(r.get("이름", "")).lower()
            or needle in str(r.get("연락처", "")).lower()
            or needle in str(r.get("직군", "")).lower()
        ]

    if not rows:
        st.info("표시할 신청자가 없습니다.")
        if hidden:
            if st.button("숨김 초기화", key="crm_unhide_all"):
                st.session_state["crm_hidden_rows"] = set()
                st.rerun()
        return

    # 테이블 + 삭제(숨기기) 버튼
    show_cols = ["신청일", "이름", "연락처", "단계", "입금", "매칭", "거절", "환불", "D-day", "직군", "지역", "행"]
    show_cols = [c for c in show_cols if c in pd.DataFrame(rows).columns]
    table = pd.DataFrame(rows)[show_cols]

    col_cfg: dict[str, Any] = {}
    if "행" in table.columns:
        col_cfg["행"] = st.column_config.NumberColumn("행#", width="small")
    if "단계" in table.columns:
        col_cfg["단계"] = st.column_config.TextColumn("단계", width="medium")

    selected = st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
        height=min(440, 44 + len(rows) * 36),
        on_select="rerun",
        selection_mode="multi-row",
        column_config=col_cfg,
    )

    sel_indices = selected.selection.get("rows", []) if hasattr(selected, "selection") else []
    if sel_indices:
        n_sel = len(sel_indices)
        d1, d2, _ = st.columns([1, 1, 4])
        with d1:
            if st.button(f"🙈 {n_sel}명 숨기기", key="crm_hide_sel", type="secondary"):
                for i in sel_indices:
                    row_num = rows[i].get("행")
                    if row_num is not None:
                        hidden.add(row_num)
                st.session_state["crm_hidden_rows"] = hidden
                st.rerun()
        with d2:
            if hidden and st.button("숨김 전체 해제", key="crm_unhide_all2"):
                st.session_state["crm_hidden_rows"] = set()
                st.rerun()

    st.caption(
        f"총 **{len(rows)}**명 표시 · "
        f"입금 대기 **{snapshot.stage_counts.get('unpaid', 0)}** · "
        f"매칭 진행 **{snapshot.stage_counts.get('matching', 0)}** · "
        + (f"숨긴 항목 **{len(hidden)}**" if hidden else "")
    )


# ── 이벤트 초기화 ──────────────────────────────────────────────
def _render_event_reset(demo_mode: bool) -> None:
    with st.expander("⚙️ 데이터 관리", expanded=False):
        st.caption("랜딩 이벤트 파일(`data/crm_events.jsonl`)을 초기화합니다. 시트 데이터는 영향 없음.")
        event_count = len(load_events())
        st.markdown(f"현재 이벤트 **{event_count}**건 저장됨")

        if "crm_reset_confirm" not in st.session_state:
            st.session_state["crm_reset_confirm"] = False

        if not st.session_state["crm_reset_confirm"]:
            if st.button("🗑 이벤트 기록 초기화", key="crm_reset_btn", type="secondary"):
                st.session_state["crm_reset_confirm"] = True
                st.rerun()
        else:
            st.warning("⚠️ 모든 방문·클릭 이벤트 기록이 삭제됩니다. 정말 초기화할까요?")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ 확인, 초기화", key="crm_reset_confirm_yes", type="primary"):
                    if EVENTS_PATH.is_file():
                        EVENTS_PATH.write_text("", encoding="utf-8")
                    st.session_state["crm_reset_confirm"] = False
                    st.success("초기화 완료!")
                    st.rerun()
            with c2:
                if st.button("취소", key="crm_reset_cancel"):
                    st.session_state["crm_reset_confirm"] = False
                    st.rerun()


# ── 메인 진입점 ──────────────────────────────────────────────
def render_crm_tab(*, raw_df: pd.DataFrame, demo_mode: bool) -> None:
    events = crm_events_for_mode(demo_mode=demo_mode)
    snapshot = build_crm_snapshot(raw_df, events=events)

    # 헤더
    h1, h2 = st.columns([5, 1])
    with h1:
        st.markdown("#### CRM · 전환 퍼널")
        st.caption(
            "랜딩 **방문·신청 클릭**은 자동 수집 · **폼·입금·매칭·환불**은 구글 시트 기준. "
            f"참가비 {PARTICIPATION_FEE} · 입금 {snapshot.revenue_paid:,}원 · 환불 {snapshot.revenue_refunded:,}원"
        )

    # 전환율 요약 바
    _render_conversion_summary(snapshot)
    st.markdown('<div style="margin:12px 0 4px"></div>', unsafe_allow_html=True)

    # KPI 카드
    _render_kpis(snapshot)
    st.markdown('<div class="crm-section-gap"></div>', unsafe_allow_html=True)

    # 단계 칩
    _render_stage_chips(snapshot)
    st.markdown("---")

    # 퍼널 + 차트
    left, right = st.columns([11, 9], gap="large")

    with left:
        st.markdown("##### 퍼널 상세")
        _render_funnel(snapshot)

    with right:
        chart_tab1, chart_tab2, chart_tab3 = st.tabs(["📈 일별 추이", "📊 단계 분포", "📋 이벤트 로그"])

        with chart_tab1:
            if snapshot.event_summary.get("by_day") or snapshot.daily_applicants:
                days = sorted(
                    set(snapshot.event_summary.get("by_day", {}).keys())
                    | set(snapshot.daily_applicants.keys())
                )
                chart_rows = []
                for d in days[-14:]:
                    ev = snapshot.event_summary.get("by_day", {}).get(d, {})
                    chart_rows.append({
                        "날짜": d,
                        "방문": ev.get("page_view", 0),
                        "신청클릭": ev.get("apply_click", 0),
                        "폼제출": snapshot.daily_applicants.get(d, 0),
                    })
                if chart_rows:
                    st.line_chart(
                        pd.DataFrame(chart_rows).set_index("날짜"),
                        height=220,
                        color=["#3b82f6", "#8b5cf6", "#10b981"],
                    )
                else:
                    st.caption("아직 일별 데이터가 없습니다.")
            else:
                st.caption("이벤트·신청 데이터가 쌓이면 차트가 표시됩니다.")

        with chart_tab2:
            _render_stage_bar(snapshot)
            # 전환율 비교 표
            ev = snapshot.event_summary.get("unique", {})
            pv = ev.get("page_view", 0)
            ac = ev.get("apply_click", 0)
            fm = snapshot.form_total
            sc = snapshot.stage_counts
            paid = sc.get("matching", 0) + sc.get("reject_1", 0) + sc.get("matched", 0) + sc.get("closed", 0)
            matched = sc.get("matched", 0)

            def _p(n: int, d: int) -> str:
                return f"{round(n/d*100,1)}%" if d else "—"

            rate_df = pd.DataFrame([
                {"구간": "방문 → 신청클릭", "전환율": _p(ac, pv)},
                {"구간": "신청클릭 → 폼제출", "전환율": _p(fm, ac)},
                {"구간": "폼제출 → 입금", "전환율": _p(paid, fm)},
                {"구간": "입금 → 매칭완료", "전환율": _p(matched, paid)},
                {"구간": "방문 → 최종매칭", "전환율": _p(matched, pv)},
            ])
            st.dataframe(rate_df, hide_index=True, use_container_width=True, height=210)

        with chart_tab3:
            recent: list[dict[str, Any]] = snapshot.event_summary.get("recent", [])
            if not recent:
                st.caption("수집된 이벤트 없음 — 랜딩 페이지 방문 후 표시됩니다.")
            else:
                log_rows = [
                    {
                        "시각": str(r.get("ts", ""))[:19].replace("T", " "),
                        "이벤트": r.get("event", "—"),
                        "visitor_id": str(r.get("visitor_id", "—"))[:14],
                    }
                    for r in recent[:20]
                ]
                st.dataframe(pd.DataFrame(log_rows), hide_index=True, use_container_width=True, height=220)
            st.caption(f"파일: `{EVENTS_PATH.name}`")

    st.markdown("---")

    # 신청자 테이블
    _render_applicant_table(snapshot, raw_df)

    st.markdown("---")
    _render_event_reset(demo_mode)
