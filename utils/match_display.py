"""
매칭 키워드 분석 — 설문 필드 기준 일치 항목 시각화
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd

from utils.columns import cell

# 설문 항목 ↔ 논리 키
SURVEY_FIELDS = {
    "job": "메인 직군",
    "region": "활동 지역",
    "years": "연차",
    "depth": "협업 깊이",
    "gender": "성별",
    "values": "가치관",
    "have": "제공 가치",
    "want": "원하는 것",
    "w_job": "희망 직군",
    "w_region": "희망 지역",
    "w_years": "희망 연차",
    "w_gender": "희망 성별",
}


@dataclass
class MatchKeyword:
    key: str
    label: str
    matched: bool
    keyword: str
    filter_field: str
    filter_value: str


def kw_short(text: str, n: int = 11) -> str:
    s = str(text or "").strip()
    if not s or s in ("무관", "nan", "None"):
        return "—"
    if "(" in s:
        s = s.split("(")[0]
    if "/" in s:
        s = s.split("/")[0]
    s = s.strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def _tokens(text: str) -> set[str]:
    return {w for w in re.findall(r"[\w가-힣]{2,}", str(text)) if len(w) >= 2}


def _theme(text: str) -> str:
    s = str(text).strip()
    return s.split("(")[0].strip() if "(" in s else s[:40]


def job_match(want: str, actual: str) -> bool:
    if not want or not actual:
        return False
    want, actual = str(want).strip(), str(actual).strip()
    if want in ("무관", "기타"):
        return False
    wm = want.split("(")[0].strip()
    am = actual.split("(")[0].strip()
    return wm == am or wm in actual or am in want


def region_ok(want: str, actual: str) -> bool:
    want = str(want).strip()
    actual = str(actual).strip()
    if want in ("", "무관", "무관(온라인)"):
        return True
    return want == actual or want in actual or actual in want


def gender_ok(want: str, actual: str) -> bool:
    want = str(want).strip()
    return want in ("", "무관") or want == str(actual).strip()


def years_ok(want: str, actual: str) -> bool:
    want, actual = str(want).strip(), str(actual).strip()
    return bool(want) and want not in ("무관",) and want == actual


def values_align(a: str, b: str) -> bool:
    ta, tb = _theme(a), _theme(b)
    if not ta or not tb:
        return False
    if ta == tb:
        return True
    wa, wb = _tokens(ta), _tokens(tb)
    return len(wa & wb) >= 2 or any(len(w) >= 4 and w in tb for w in wa)


def need_met(need: str, offer: str) -> bool:
    if not need or not offer:
        return False
    need, offer = str(need).strip(), str(offer).strip()
    if len(need) < 4:
        return False
    wn, wo = _tokens(need), _tokens(offer)
    if len(wn & wo) >= 2:
        return True
    return any(w in offer for w in wn if len(w) >= 3)


def analyze_pair(me: pd.Series, other: pd.Series) -> list[MatchKeyword]:
    """me 기준으로 other와의 항목별 일치 분석."""
    items: list[MatchKeyword] = []

    my_wjob = cell(me, "w_job")
    ot_job = cell(other, "job")
    jm = job_match(my_wjob, ot_job)
    items.append(MatchKeyword(
        "job", "직군", jm, kw_short(ot_job if jm else my_wjob),
        "job", kw_short(ot_job if jm else my_wjob, 20),
    ))

    my_wreg = cell(me, "w_region")
    ot_reg = cell(other, "region")
    rm = region_ok(my_wreg, ot_reg)
    items.append(MatchKeyword(
        "region", "지역", rm, kw_short(ot_reg if rm else my_wreg),
        "region", str(ot_reg if rm else my_wreg)[:20],
    ))

    my_wyrs = cell(me, "w_years")
    ot_yrs = cell(other, "years")
    ym = years_ok(my_wyrs, ot_yrs)
    items.append(MatchKeyword(
        "years", "연차", ym, kw_short(ot_yrs if ym else my_wyrs, 8),
        "years", str(ot_yrs if ym else my_wyrs)[:20],
    ))

    my_dep = cell(me, "depth")
    ot_dep = cell(other, "depth")
    dm = bool(my_dep and my_dep == ot_dep)
    items.append(MatchKeyword(
        "depth", "협업깊이", dm, kw_short(my_dep if dm else my_dep, 8),
        "depth", _theme(my_dep)[:20],
    ))

    my_wgen = cell(me, "w_gender")
    ot_gen = cell(other, "gender")
    gm = gender_ok(my_wgen, ot_gen)
    items.append(MatchKeyword(
        "gender", "성별", gm, str(ot_gen if gm else my_wgen)[:4],
        "gender", str(ot_gen)[:10],
    ))

    my_val = cell(me, "values")
    ot_val = cell(other, "values")
    vm = values_align(my_val, ot_val)
    vk = kw_short(my_val if vm else my_val, 8)
    items.append(MatchKeyword(
        "values", "가치관", vm, vk,
        "values", _theme(my_val)[:20],
    ))

    my_want = cell(me, "want")
    ot_have = cell(other, "have")
    nm = need_met(my_want, ot_have)
    items.append(MatchKeyword(
        "need", "원함↔제공", nm, "맞음" if nm else "—",
        "have", kw_short(ot_have, 20),
    ))

    # 역방향
    rj = job_match(cell(other, "w_job"), cell(me, "job"))
    items.append(MatchKeyword(
        "r_job", "상대희망직군", rj, kw_short(cell(me, "job")),
        "w_job", kw_short(cell(other, "w_job"), 20),
    ))

    rn = need_met(cell(other, "want"), cell(me, "have"))
    items.append(MatchKeyword(
        "r_need", "상대원함↔내제공", rn, "맞음" if rn else "—",
        "want", kw_short(cell(other, "want"), 20),
    ))

    return items


def score_from_keywords(items: list[MatchKeyword]) -> tuple[int, bool]:
    weights = {
        "job": 28, "region": 18, "years": 14, "depth": 10,
        "gender": 5, "values": 12, "need": 15,
        "r_job": 22, "r_need": 14,
    }
    score = sum(weights.get(it.key, 0) for it in items if it.matched)
    fwd_job = any(it.matched and it.key == "job" for it in items)
    rev_job = any(it.matched and it.key == "r_job" for it in items)
    mutual = fwd_job and rev_job
    return score, mutual


def keywords_html(items: list[MatchKeyword]) -> str:
    parts = []
    for it in items:
        cls = "kw-card kw-yes" if it.matched else "kw-card kw-no"
        if it.matched:
            if it.keyword in ("—", ""):
                detail = "일치"
            elif it.keyword == "맞음":
                detail = "맞음"
            else:
                detail = it.keyword
        else:
            detail = "—"
        parts.append(
            f'<div class="{cls}">'
            f'<span class="kw-lbl">{it.label}</span>'
            f'<span class="kw-val">{detail}</span>'
            f"</div>"
        )
    return f'<div class="kw-grid">{"".join(parts)}</div>'


def apply_keyword_filter(frame: pd.DataFrame, flt: dict | None) -> pd.DataFrame:
    if not flt:
        return frame
    field = flt.get("field", "")
    val = str(flt.get("value", "")).strip()
    if not field or not val or field not in frame.columns:
        return frame
    col = frame[field].astype(str)
    if field in ("region", "w_region", "years", "gender"):
        return frame[col.str.contains(re.escape(val), case=False, na=False)]
    return frame[col.str.contains(re.escape(val[:15]), case=False, na=False)]
