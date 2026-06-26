"""
매칭 추천 — 희망 조건 · 가치관 · Have/Want · 양방향 적합
"""
from __future__ import annotations

import pandas as pd

from utils.columns import cell, parse_reject
from utils.match_display import MatchKeyword, analyze_pair, score_from_keywords
from utils.value_match import ValueMatchResult, compute_value_match

C_MATCHED = "matched"
C_REJECT = "reject"


class MatchCandidate:
    __slots__ = ("idx", "score", "reasons", "mutual", "keywords", "value")

    def __init__(
        self,
        idx: int = -1,
        score: int = 0,
        reasons: list[str] | None = None,
        mutual: bool = False,
        keywords: list[MatchKeyword] | None = None,
        value: ValueMatchResult | None = None,
    ):
        self.idx = idx
        self.score = score
        self.reasons = reasons or []
        self.mutual = mutual
        self.keywords = keywords or []
        self.value = value


def evaluate(me: pd.Series, other: pd.Series) -> MatchCandidate:
    kws = analyze_pair(me, other)
    score, mutual = score_from_keywords(kws)
    reasons = [f"{k.label} {k.keyword}" for k in kws if k.matched]
    if mutual:
        reasons.insert(0, "양방향 적합")
    vm = compute_value_match(me, other)
    return MatchCandidate(score=score, reasons=reasons, mutual=mutual, keywords=kws, value=vm)


def recommend(me_idx: int, df: pd.DataFrame, top_n: int = 3) -> list[MatchCandidate]:
    me = df.loc[me_idx]
    out: list[MatchCandidate] = []

    for idx, row in df.iterrows():
        if idx == me_idx:
            continue
        if str(cell(row, C_MATCHED, "")).strip().upper() == "TRUE":
            continue
        if parse_reject(cell(row, C_REJECT, 0)) >= 2:
            continue
        cand = evaluate(me, row)
        cand.idx = idx
        if cand.value and cand.value.pct > 0:
            out.append(cand)

    out.sort(key=lambda c: (c.value.pct if c.value else 0, c.mutual, c.score), reverse=True)
    return out[:top_n]


def score_label(score: int, mutual: bool = False) -> str:
    if mutual and score >= 70:
        return "양방향 · 매우 적합"
    if score >= 75:
        return "매우 적합"
    if score >= 50:
        return "적합"
    if score >= 30:
        return "검토 가능"
    return "낮음"
