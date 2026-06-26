"""빠른 실시간 검색 — 단일 인덱스 컬럼"""
from __future__ import annotations

import pandas as pd

SEARCH_FIELDS = (
    "name",
    "job",
    "region",
    "years",
    "gender",
    "contact",
    "have",
    "want",
    "w_job",
    "w_region",
    "values",
    "depth",
    "note",
)


def build_search_blob(frame: pd.DataFrame) -> pd.Series:
    """행별 검색용 문자열 (소문자) — 벡터 연산 1회."""
    cols = [c for c in SEARCH_FIELDS if c in frame.columns]
    if not cols:
        return pd.Series("", index=frame.index)
    blob = frame[cols[0]].fillna("").astype(str)
    for col in cols[1:]:
        blob = blob + " " + frame[col].fillna("").astype(str)
    return blob.str.lower()


def ensure_search_index(frame: pd.DataFrame) -> pd.DataFrame:
    if "_search" in frame.columns:
        return frame
    out = frame.copy()
    out["_search"] = build_search_blob(out)
    return out


def drop_search_index(frame: pd.DataFrame) -> pd.DataFrame:
    if "_search" not in frame.columns:
        return frame
    return frame.drop(columns=["_search"])


def search_df(frame: pd.DataFrame, query: str) -> pd.DataFrame:
    q = query.strip().lower()
    if not q or frame.empty:
        return frame
    indexed = ensure_search_index(frame)
    return indexed[indexed["_search"].str.contains(q, na=False, regex=False)]
