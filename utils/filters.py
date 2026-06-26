"""
목록 필터 — 설문 필드별 값 선택
"""
from __future__ import annotations

import pandas as pd

from utils.match_display import _theme

# key, label, 표시용 그룹
FILTER_FIELDS: list[tuple[str, str]] = [
    ("gender", "성별"),
    ("job", "직군"),
    ("region", "활동 지역"),
    ("years", "연차"),
    ("w_job", "희망 직군"),
    ("w_region", "희망 지역"),
    ("w_years", "희망 연차"),
    ("w_gender", "희망 성별"),
    ("values", "가치관"),
    ("depth", "협업 깊이"),
]

FILTER_KEYS = [k for k, _ in FILTER_FIELDS]


def option_label(field: str, value: str) -> str:
    v = str(value or "").strip()
    if not v or v.lower() == "nan":
        return "—"
    if field in ("job", "w_job"):
        if "(" in v:
            v = v.split("(")[0].strip()
        return v if len(v) <= 18 else v[:17] + "…"
    if field in ("values", "depth", "want"):
        t = _theme(v)
        return t if len(t) <= 22 else t[:21] + "…"
    return v if len(v) <= 24 else v[:23] + "…"


def field_options(df: pd.DataFrame, field: str) -> list[str]:
    if field not in df.columns:
        return []
    vals = (
        df[field]
        .dropna()
        .astype(str)
        .str.strip()
        .loc[lambda s: s.ne("") & s.ne("nan") & s.ne("None")]
    )
    return sorted(vals.unique().tolist(), key=str)


def collect_filter_selections() -> dict[str, list[str]]:
    import streamlit as st

    out: dict[str, list[str]] = {}
    for key in FILTER_KEYS:
        sel = st.session_state.get(f"flt_{key}", [])
        if sel:
            out[key] = list(sel)
    return out


def apply_field_filters(frame: pd.DataFrame, selections: dict[str, list[str]]) -> pd.DataFrame:
    out = frame
    for key, picked in selections.items():
        if not picked or key not in out.columns:
            continue
        col = out[key].astype(str).str.strip()
        out = out[col.isin(picked)]
    return out


def active_filter_labels(selections: dict[str, list[str]]) -> list[str]:
    labels = {k: v for k, v in FILTER_FIELDS}
    chips: list[str] = []
    for key, picked in selections.items():
        lbl = labels.get(key, key)
        for val in picked:
            chips.append(f"{lbl}: {option_label(key, val)}")
    return chips


def clear_all_filters() -> None:
    import streamlit as st

    from utils.date_filter import reset_date_filter

    for key in FILTER_KEYS:
        st.session_state[f"flt_{key}"] = []
    st.session_state["chip_filter"] = None
    reset_date_filter()
