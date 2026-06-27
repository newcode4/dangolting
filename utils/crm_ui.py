"""CRM 대시보드 UI — 직관형 재설계."""
from __future__ import annotations

import html as html_lib
from datetime import date, timedelta
from typing import Any

import pandas as pd
import streamlit as st

from utils.crm import STAGE_LABELS, CrmSnapshot, build_crm_snapshot, crm_events_for_mode
from utils.crm_events import EVENTS_PATH, load_events
from utils.landing_config import PARTICIPATION_FEE

_STAGE_COLOR = {
    "unpaid":   "#f59e0b",
    "matching": "#6366f1",
    "reject_1": "#ef4444",
    "matched":  "#10b981",
    "closed":   "#64748b",
    "refunded": "#ec4899",
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. ACTION ALERT — 지금 당장 해야 할 일
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _render_action_alerts(snapshot: CrmSnapshot) -> None:
    sc = snapshot.stage_counts
    unpaid   = sc.get("unpaid", 0)
    matching = sc.get("matching", 0)
    reject1  = sc.get("reject_1", 0)
    refunded = sc.get("refunded", 0)

    # 다크테마 팔레트 (bg, border, text)
    alerts = []
    if unpaid:
        alerts.append(("🔴", f"입금 대기 {unpaid}명", "입금 확인 후 매칭 풀 이동 필요", "#2d1f00", "#f59e0b", "#fbbf24"))
    if reject1:
        alerts.append(("🟡", f"1차 거절 {reject1}명", "재매칭 진행 또는 상황 확인 필요", "#2d001a", "#db2777", "#f472b6"))
    if matching:
        alerts.append(("🔵", f"매칭 진행 중 {matching}명", "상대방 탐색·연결 진행 중", "#0f1f3d", "#3b82f6", "#60a5fa"))
    if refunded:
        alerts.append(("⚪", f"환불 처리 {refunded}명", "완료 케이스", "#1a1f2e", "#64748b", "#94a3b8"))

    if not alerts:
        st.success("✅ 현재 처리 대기 항목 없음")
        return

    cols = st.columns(len(alerts))
    for col, (icon, title, desc, bg, border, txt) in zip(cols, alerts):
        with col:
            st.markdown(
                f'<div style="background:{bg};border-left:4px solid {border};'
                f'border-radius:10px;padding:14px 16px;margin-bottom:4px">'
                f'<div style="font-size:18px;font-weight:900;color:{txt}">{icon} {title}</div>'
                f'<div style="font-size:12px;color:#8b949e;margin-top:4px">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. KPI 카드 — 전환율 델타 포함
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _render_kpi_row(snapshot: CrmSnapshot) -> None:
    ev = snapshot.event_summary.get("unique", {})
    sc = snapshot.stage_counts
    pv     = ev.get("page_view", 0)
    ac     = ev.get("apply_click", 0)
    fm     = snapshot.form_total
    paid   = sc.get("matching", 0) + sc.get("reject_1", 0) + sc.get("matched", 0) + sc.get("closed", 0)
    matched = sc.get("matched", 0)
    refund  = sc.get("refunded", 0)

    def pct(n: int, d: int) -> str:
        return f"{round(n/d*100,1)}%" if d else "—"

    def color(n: int, d: int) -> str:
        if not d: return "#64748b"
        r = n / d * 100
        return "#10b981" if r >= 50 else "#f59e0b" if r >= 20 else "#ef4444"

    def arrow(n: int, d: int) -> str:
        if not d: return "—"
        r = n / d * 100
        arrow_char = "↑" if r >= 50 else "↓"
        return f"{arrow_char} {round(r,1)}%"

    kpis = [
        ("👁 방문(순)",   pv,      None,              "#3b82f6",  "고유 방문자"),
        ("🖱 신청클릭",   ac,      arrow(ac, pv),     color(ac,pv),    "방문→클릭"),
        ("📝 폼제출",     fm,      arrow(fm, ac),     color(fm,ac),    "클릭→제출"),
        ("💳 입금확인",   paid,    arrow(paid, fm),   color(paid,fm),  "제출→입금"),
        ("🤝 매칭완료",   matched, arrow(matched,paid), color(matched,paid), "입금→매칭"),
        ("↩ 환불",        refund,  None,              "#ec4899",  ""),
    ]

    cols = st.columns(len(kpis))
    for col, (label, val, rate, clr, hint) in zip(cols, kpis):
        with col:
            rate_html = (
                f'<div style="font-size:11px;font-weight:700;color:{clr};margin-top:2px">'
                f'{rate}</div>' if rate and rate != "—" else ""
            )
            hint_html = (
                f'<div style="font-size:10px;color:#94a3b8;margin-top:1px">{hint}</div>'
                if hint else ""
            )
            st.markdown(
                f'<div style="background:#161b22;border:1px solid #21262d;border-top:3px solid {clr};'
                f'border-radius:10px;padding:14px 12px;text-align:center">'
                f'<div style="font-size:11px;color:#8b949e;font-weight:600;margin-bottom:6px">{label}</div>'
                f'<div style="font-size:1.6rem;font-weight:900;color:#f0f6fc;line-height:1">{val:,}</div>'
                f'{rate_html}{hint_html}'
                f'</div>',
                unsafe_allow_html=True,
            )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. 시각적 퍼널 — 가로 막대 + 드롭오프 표시
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _render_visual_funnel(snapshot: CrmSnapshot) -> None:
    max_count = max((s.count for s in snapshot.funnel), default=1) or 1
    rows_html = []

    for i, step in enumerate(snapshot.funnel):
        width_pct = max(3, int(step.count / max_count * 100))
        # 이전 대비 전환율 색상
        if step.rate_from_prev is None:
            rate_color = "#64748b"
            rate_txt = ""
        elif step.rate_from_prev >= 50:
            rate_color = "#10b981"; rate_txt = f"이전 대비 {step.rate_from_prev}% ✓"
        elif step.rate_from_prev >= 20:
            rate_color = "#f59e0b"; rate_txt = f"이전 대비 {step.rate_from_prev}%"
        else:
            rate_color = "#ef4444"; rate_txt = f"이전 대비 {step.rate_from_prev}% ▼ 낮음"

        top_txt = f"방문 대비 {step.rate_from_top}%" if step.rate_from_top is not None else ""

        # 드롭오프 계산 (다음 단계와 비교)
        drop_html = ""
        if i < len(snapshot.funnel) - 1:
            nxt = snapshot.funnel[i + 1]
            if step.count > 0 and nxt.count < step.count:
                dropped = step.count - nxt.count
                drop_pct = round(dropped / step.count * 100, 0)
                drop_html = (
                    f'<div style="text-align:right;font-size:10px;color:#ef4444;'
                    f'margin-top:2px">▼ {int(drop_pct)}% 이탈 ({dropped}명)</div>'
                )

        row = (
            f'<div style="margin-bottom:10px">'
            # 레이블 행
            f'<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:4px">'
            f'<span style="font-size:12px;color:#c9d1d9;font-weight:600">{html_lib.escape(step.label)}</span>'
            f'<div style="display:flex;gap:8px;align-items:center">'
            f'<span style="font-size:14px;color:#f0f6fc;font-weight:800">{step.count:,}</span>'
            f'<span style="font-size:11px;color:{rate_color};font-weight:700">{rate_txt}</span>'
            f'</div></div>'
            # 막대
            f'<div style="height:14px;background:#21262d;border-radius:7px;overflow:hidden;position:relative">'
            f'<div style="height:100%;width:{width_pct}%;background:linear-gradient(90deg,#1f6feb,#58a6ff);'
            f'border-radius:7px;transition:width .3s"></div>'
            f'</div>'
            # 보조 정보
            f'<div style="display:flex;justify-content:space-between">'
            f'<span style="font-size:10px;color:#6e7681">{top_txt}</span>'
            f'{drop_html}'
            f'</div>'
            f'</div>'
        )
        rows_html.append(row)

    st.markdown(f'<div>{"".join(rows_html)}</div>', unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. Plotly 꺾은선 차트 + 날짜 필터
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _render_trend_chart(snapshot: CrmSnapshot) -> None:
    try:
        import plotly.graph_objects as go
    except ImportError:
        st.caption("plotly 미설치 — `pip install plotly`")
        return

    by_day   = snapshot.event_summary.get("by_day", {})
    daily_fm = snapshot.daily_applicants

    all_days = sorted(set(by_day.keys()) | set(daily_fm.keys()))
    if not all_days:
        st.caption("데이터가 쌓이면 차트가 표시됩니다.")
        return

    # 날짜 범위 필터
    d_min = date.fromisoformat(all_days[0])
    d_max = date.fromisoformat(all_days[-1])
    d_default_start = max(d_min, d_max - timedelta(days=29))

    fc1, fc2 = st.columns(2)
    with fc1:
        d_start = st.date_input("시작일", value=d_default_start, min_value=d_min, max_value=d_max, key="crm_date_start")
    with fc2:
        d_end = st.date_input("종료일", value=d_max, min_value=d_min, max_value=d_max, key="crm_date_end")

    if d_start > d_end:
        st.warning("시작일이 종료일보다 늦습니다.")
        return

    filtered_days = [
        d for d in all_days
        if date.fromisoformat(d) >= d_start and date.fromisoformat(d) <= d_end
    ]

    pv_vals  = [by_day.get(d, {}).get("page_view",   0) for d in filtered_days]
    ac_vals  = [by_day.get(d, {}).get("apply_click", 0) for d in filtered_days]
    fm_vals  = [daily_fm.get(d, 0)                      for d in filtered_days]

    fig = go.Figure()

    def add_line(name, y, color, dash="solid", fill=None):
        fig.add_trace(go.Scatter(
            x=filtered_days, y=y, name=name,
            mode="lines+markers",
            line=dict(color=color, width=2.5, dash=dash),
            marker=dict(size=6, color=color, line=dict(color="#0d1117", width=1.5)),
            fill=fill,
            fillcolor=color.replace(")", ",0.07)").replace("rgb", "rgba") if fill else None,
            hovertemplate=f"<b>{name}</b><br>%{{x}}: %{{y}}명<extra></extra>",
        ))

    add_line("방문(순)",   pv_vals,  "#3b82f6", fill="tozeroy")
    add_line("신청클릭",   ac_vals,  "#8b5cf6")
    add_line("폼제출",     fm_vals,  "#10b981", dash="dot")

    fig.update_layout(
        height=240,
        margin=dict(l=0, r=0, t=8, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8b949e", size=11),
        legend=dict(
            orientation="h", y=-0.18, x=0,
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="#c9d1d9", size=11),
        ),
        xaxis=dict(
            showgrid=False, zeroline=False,
            tickfont=dict(color="#6e7681", size=10),
            tickangle=-30,
        ),
        yaxis=dict(
            showgrid=True, zeroline=False,
            gridcolor="rgba(255,255,255,0.05)",
            tickfont=dict(color="#6e7681", size=10),
        ),
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # 기간 합계 요약
    total_pv = sum(pv_vals)
    total_ac = sum(ac_vals)
    total_fm = sum(fm_vals)
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("기간 방문", f"{total_pv:,}명")
    s2.metric("기간 신청클릭", f"{total_ac:,}명",
              delta=f"{round(total_ac/total_pv*100,1)}% 전환" if total_pv else None)
    s3.metric("기간 폼제출", f"{total_fm:,}명",
              delta=f"{round(total_fm/total_ac*100,1)}% 전환" if total_ac else None)
    s4.metric("선택 기간", f"{(d_end - d_start).days + 1}일")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. 단계 분포 도넛 차트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _render_stage_donut(snapshot: CrmSnapshot) -> None:
    try:
        import plotly.graph_objects as go
    except ImportError:
        return

    sc = snapshot.stage_counts
    keys   = ["unpaid", "matching", "reject_1", "matched", "closed", "refunded"]
    labels = [STAGE_LABELS.get(k, k) for k in keys]
    values = [sc.get(k, 0) for k in keys]
    colors = [_STAGE_COLOR.get(k, "#64748b") for k in keys]

    if sum(values) == 0:
        st.caption("신청자 없음")
        return

    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        hole=0.55,
        marker=dict(colors=colors, line=dict(color="#0d1117", width=2)),
        textinfo="percent+label",
        textfont=dict(size=11, color="#c9d1d9"),
        hovertemplate="<b>%{label}</b><br>%{value}명 (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        height=240,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        annotations=[dict(
            text=f"총<br><b>{sum(values)}</b>명",
            x=0.5, y=0.5, font=dict(size=14, color="#f0f6fc"), showarrow=False,
        )],
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. 신청자 테이블 (soft delete)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _render_applicant_table(snapshot: CrmSnapshot) -> None:
    st.markdown("##### 📋 신청자 파이프라인")

    if "crm_hidden_rows" not in st.session_state:
        st.session_state["crm_hidden_rows"] = set()
    hidden: set = st.session_state["crm_hidden_rows"]

    fa, fb, fc, fd = st.columns([3, 2, 1, 1])
    with fa:
        stage_filter = st.multiselect(
            "단계 필터", options=list(STAGE_LABELS.values()),
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
            st.session_state["crm_hidden_rows"] = set(); st.rerun()

    rows = snapshot.applicants
    if not show_hidden:
        rows = [r for r in rows if r.get("행") not in hidden]
    if stage_filter:
        allowed = set(stage_filter)
        rows = [r for r in rows if r.get("단계") in allowed]
    if q.strip():
        needle = q.strip().lower()
        rows = [r for r in rows
                if needle in str(r.get("이름","")).lower()
                or needle in str(r.get("연락처","")).lower()
                or needle in str(r.get("직군","")).lower()]

    if not rows:
        st.info("표시할 신청자가 없습니다.")
        return

    show_cols = ["신청일","이름","연락처","단계","입금","매칭","거절","환불","D-day","직군","지역","행"]
    tbl = pd.DataFrame(rows)
    show_cols = [c for c in show_cols if c in tbl.columns]

    sel = st.dataframe(
        tbl[show_cols], use_container_width=True, hide_index=True,
        height=min(440, 44 + len(rows) * 36),
        on_select="rerun", selection_mode="multi-row",
    )
    sel_idx = sel.selection.get("rows", []) if hasattr(sel, "selection") else []
    if sel_idx:
        if st.button(f"🙈 {len(sel_idx)}명 목록에서 숨기기", key="crm_hide_sel", type="secondary"):
            for i in sel_idx:
                rn = rows[i].get("행")
                if rn is not None:
                    hidden.add(rn)
            st.session_state["crm_hidden_rows"] = hidden; st.rerun()

    st.caption(
        f"표시 **{len(rows)}**명 · 입금 대기 **{snapshot.stage_counts.get('unpaid',0)}** · "
        f"매칭 진행 **{snapshot.stage_counts.get('matching',0)}**"
        + (f" · 숨김 **{len(hidden)}**" if hidden else "")
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. 이벤트 초기화
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _render_event_reset(demo_mode: bool) -> None:
    with st.expander("⚙️ 데이터 관리", expanded=False):
        event_count = len(load_events())
        st.caption(f"랜딩 이벤트 파일(`{EVENTS_PATH.name}`) — 현재 **{event_count}**건")
        if "crm_reset_confirm" not in st.session_state:
            st.session_state["crm_reset_confirm"] = False
        if not st.session_state["crm_reset_confirm"]:
            if st.button("🗑 이벤트 기록 초기화", key="crm_reset_btn", type="secondary"):
                st.session_state["crm_reset_confirm"] = True; st.rerun()
        else:
            st.warning("⚠️ 모든 방문·클릭 이벤트 기록이 삭제됩니다. 계속할까요?")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ 초기화 확인", key="crm_reset_yes", type="primary"):
                    if EVENTS_PATH.is_file():
                        EVENTS_PATH.write_text("", encoding="utf-8")
                    st.session_state["crm_reset_confirm"] = False
                    st.success("초기화 완료!"); st.rerun()
            with c2:
                if st.button("취소", key="crm_reset_cancel"):
                    st.session_state["crm_reset_confirm"] = False; st.rerun()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def render_crm_tab(*, raw_df: pd.DataFrame, demo_mode: bool) -> None:
    events   = crm_events_for_mode(demo_mode=demo_mode)
    snapshot = build_crm_snapshot(raw_df, events=events)

    # ── 헤더 ──
    st.markdown("#### CRM · 전환 퍼널")
    st.caption(
        f"참가비 {PARTICIPATION_FEE} · "
        f"총 입금 **{snapshot.revenue_paid:,}원** · "
        f"환불 **{snapshot.revenue_refunded:,}원** · "
        f"순수익 **{snapshot.revenue_paid - snapshot.revenue_refunded:,}원**"
    )
    st.markdown("---")

    # ── 1. 지금 할 일 ──
    st.markdown("##### 🚨 지금 처리 필요")
    _render_action_alerts(snapshot)
    st.markdown('<div style="margin:16px 0"></div>', unsafe_allow_html=True)

    # ── 2. KPI ──
    st.markdown("##### 📊 전환 현황")
    _render_kpi_row(snapshot)
    st.markdown('<div style="margin:20px 0 4px"></div>', unsafe_allow_html=True)

    # ── 3. 퍼널 + 도넛 ──
    left, right = st.columns([13, 7], gap="large")
    with left:
        st.markdown("##### 🔽 퍼널 상세 (드롭오프 포함)")
        _render_visual_funnel(snapshot)
    with right:
        st.markdown("##### 🥧 단계 분포")
        _render_stage_donut(snapshot)

    st.markdown("---")

    # ── 4. 꺾은선 추이 ──
    st.markdown("##### 📈 일별 추이 (날짜 선택 가능)")
    _render_trend_chart(snapshot)
    st.markdown("---")

    # ── 5. 신청자 테이블 ──
    _render_applicant_table(snapshot)
    st.markdown("---")

    # ── 6. 데이터 관리 ──
    _render_event_reset(demo_mode)
