"""신청일(시간) 기준 전체 기간 필터"""
from __future__ import annotations

import re
from datetime import date, timedelta

import pandas as pd
import streamlit as st

PRESETS = ["전체", "오늘", "최근 7일", "최근 30일", "날짜 지정"]


def parse_ts(val) -> date | None:
    s = str(val or "").strip()
    if not s or s.lower() in ("nan", "none", ""):
        return None
    try:
        dt = pd.to_datetime(s, errors="coerce")
        if pd.notna(dt):
            return dt.date()  # type: ignore[union-attr]
    except Exception:
        pass
    m = re.match(r"(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})", s)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None


def date_bounds(frame: pd.DataFrame) -> tuple[date, date]:
    if "ts" not in frame.columns:
        today = date.today()
        return today, today
    valid = [d for d in frame["ts"].map(parse_ts) if d is not None]
    if not valid:
        today = date.today()
        return today, today
    return min(valid), max(valid)


def preset_range(preset: str, min_d: date, max_d: date) -> tuple[date | None, date | None]:
    today = date.today()
    if preset == "전체":
        return None, None
    if preset == "오늘":
        return today, today
    if preset == "최근 7일":
        return today - timedelta(days=6), today
    if preset == "최근 30일":
        return today - timedelta(days=29), today
    if preset == "날짜 지정":
        start = st.session_state.get("date_from", min_d)
        end = st.session_state.get("date_to", max_d)
        if isinstance(start, date) and isinstance(end, date) and start > end:
            start, end = end, start
        return start, end
    return None, None


def apply_date_filter(
    frame: pd.DataFrame,
    start: date | None,
    end: date | None,
) -> pd.DataFrame:
    if start is None and end is None:
        return frame
    if "ts" not in frame.columns:
        return frame
    parsed = frame["ts"].map(parse_ts)
    mask = parsed.notna()
    if start is not None:
        mask &= parsed >= start
    if end is not None:
        mask &= parsed <= end
    return frame[mask]


def _range_label(start: date | None, end: date | None) -> str:
    if start is None and end is None:
        return "전체 기간"
    if start == end:
        return start.strftime("%Y.%m.%d") if start else "전체 기간"
    s = start.strftime("%Y.%m.%d") if start else "…"
    e = end.strftime("%Y.%m.%d") if end else "…"
    return f"{s} ~ {e}"


def render_global_date_filter(frame: pd.DataFrame) -> tuple[date | None, date | None]:
    """상단 큰 기간 필터 — (시작일, 종료일) 반환."""
    min_d, max_d = date_bounds(frame)
    if "date_preset" not in st.session_state:
        st.session_state["date_preset"] = "전체"

    with st.container(border=True):
        st.markdown(
            '<div class="global-date-head">'
            '<span class="global-date-title">신청 기간</span>'
            '<span class="global-date-sub">구글 폼 제출일 기준</span>'
            "</div>",
            unsafe_allow_html=True,
        )

        preset = st.radio(
            "기간",
            PRESETS,
            horizontal=True,
            label_visibility="collapsed",
            key="date_preset",
        )

        start, end = preset_range(preset, min_d, max_d)

        if preset == "날짜 지정":
            c1, c2 = st.columns(2)
            with c1:
                st.date_input(
                    "시작일",
                    value=min_d,
                    min_value=min_d,
                    max_value=max_d,
                    key="date_from",
                    format="YYYY.MM.DD",
                )
            with c2:
                st.date_input(
                    "종료일",
                    value=max_d,
                    min_value=min_d,
                    max_value=max_d,
                    key="date_to",
                    format="YYYY.MM.DD",
                )
            start, end = preset_range(preset, min_d, max_d)

        filtered_n = len(apply_date_filter(frame, start, end))
        total_n = len(frame)
        label = _range_label(start, end)
        st.markdown(
            f'<div class="global-date-foot">'
            f'<span class="date-range-chip">{label}</span>'
            f'<span class="date-count"><b>{filtered_n}</b> / {total_n}명</span>'
            f"</div>",
            unsafe_allow_html=True,
        )

    return start, end


def reset_date_filter() -> None:
    st.session_state["date_preset"] = "전체"
