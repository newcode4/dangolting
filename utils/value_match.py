"""
가치 매칭률(%) — Want/Have · 깊이 · 가치관 · 지역/성별
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from utils.columns import cell
from utils.match_display import _theme, _tokens, gender_ok, need_met, region_ok

# 협업 깊이 단계 (설문 순서)
DEPTH_LEVELS: tuple[str, ...] = (
    "가벼운 의견과 피드백",
    "실질적인 작업 및 액션 지원",
    "깊이 있는 자문과 매운맛 검토",
)

# 상호 보완 가치관 (각 set은 테마 앞부분 키워드)
COMPLEMENTARY_VALUES: tuple[frozenset[str], ...] = (
    frozenset({"진정성", "신뢰"}),
    frozenset({"속도", "실행"}),
    frozenset({"완벽", "퀄리티", "전문"}),
    frozenset({"혁신", "아이디어"}),
)

WEIGHTS = {
    "want_have": 0.40,
    "depth": 0.30,
    "values": 0.20,
    "locale": 0.10,
}


@dataclass
class ValueMatchResult:
    pct: int
    tier: str  # high | mid | caution | low
    tier_title: str
    guide_icon: str
    guide_label: str
    story: str
    breakdown: dict[str, int]
    mutual_want_have: bool


def _depth_level(text: str) -> int | None:
    t = _theme(str(text or ""))
    for i, label in enumerate(DEPTH_LEVELS):
        if label in t or t.startswith(label[:6]):
            return i
    return None


def _depth_component(me: pd.Series, other: pd.Series) -> int:
    """0~100. 완전 일치 100, 1단계 차 50, 2단계 차 0."""
    a = _depth_level(cell(me, "depth"))
    b = _depth_level(cell(other, "depth"))
    if a is None or b is None:
        return 50
    diff = abs(a - b)
    if diff == 0:
        return 100
    if diff == 1:
        return 50
    return 0


def _want_have_one(want: str, have: str) -> int:
    if need_met(want, have):
        return 100
    wn, wo = _tokens(want), _tokens(have)
    if not wn or not wo:
        return 0
    overlap = len(wn & wo)
    if overlap >= 2:
        return 70
    if overlap >= 1:
        return 40
    return 0


def _want_have_component(me: pd.Series, other: pd.Series) -> tuple[int, bool]:
    fwd = _want_have_one(cell(me, "want"), cell(other, "have"))
    rev = _want_have_one(cell(other, "want"), cell(me, "have"))
    return (fwd + rev) // 2, fwd >= 70 and rev >= 70


def _value_theme_key(text: str) -> str:
    t = _theme(str(text or ""))
    if "진정" in t or "신뢰" in t or "단골" in t:
        return "진정성"
    if "속도" in t or "실행" in t:
        return "속도"
    if "완벽" in t or "퀄리티" in t or "전문" in t:
        return "완벽"
    if "혁신" in t or "아이디어" in t or "차별" in t:
        return "혁신"
    return t[:8]


def _values_complementary(a: str, b: str) -> bool:
    ka, kb = _value_theme_key(a), _value_theme_key(b)
    if ka == kb:
        return False
    for pair in COMPLEMENTARY_VALUES:
        if (ka in pair or any(k in _theme(a) for k in pair)) and (
            kb in pair or any(k in _theme(b) for k in pair)
        ):
            return True
    return False


def _values_component(me: pd.Series, other: pd.Series) -> int:
    va, vb = cell(me, "values"), cell(other, "values")
    if not va or not vb:
        return 0
    if _theme(va) == _theme(vb) or _value_theme_key(va) == _value_theme_key(vb):
        return 100
    if _values_complementary(va, vb):
        return 50
    wa, wb = _tokens(_theme(va)), _tokens(_theme(vb))
    if len(wa & wb) >= 2:
        return 80
    return 0


def _locale_component(me: pd.Series, other: pd.Series) -> int:
    r_fwd = region_ok(cell(me, "w_region"), cell(other, "region"))
    r_rev = region_ok(cell(other, "w_region"), cell(me, "region"))
    g_fwd = gender_ok(cell(me, "w_gender"), cell(other, "gender"))
    g_rev = gender_ok(cell(other, "w_gender"), cell(me, "gender"))

    score = 0.0
    if r_fwd and r_rev:
        score += 50
    elif r_fwd or r_rev:
        score += 25
    if g_fwd and g_rev:
        score += 50
    elif g_fwd or g_rev:
        score += 25
    return int(min(100, score))


def _short_job(text: str) -> str:
    s = str(text or "").split("(")[0].strip()
    return s.split("/")[0].strip()[:16] or "—"


def _years_short(text: str) -> str:
    return str(text or "무관").replace("연차 ", "")


def _story_for_tier(
    tier: str,
    me: pd.Series,
    other: pd.Series,
    breakdown: dict[str, int],
) -> tuple[str, str, str, str]:
    """title, icon, guide_label, story"""
    na = str(cell(me, "name", "A"))
    nb = str(cell(other, "name", "B"))
    my_want = _theme(cell(me, "want"))[:80]
    ot_have = _theme(cell(other, "have"))[:60]
    my_have = _theme(cell(me, "have"))[:60]
    ot_want = _theme(cell(other, "want"))[:80]
    my_val = _theme(cell(me, "values"))[:24]
    my_dep = _theme(cell(me, "depth"))[:20]
    ot_dep = _theme(cell(other, "depth"))[:20]
    my_yrs = _years_short(cell(me, "years"))
    ot_yrs = _years_short(cell(other, "years"))
    ot_job = _short_job(cell(other, "job"))

    if tier == "high":
        return (
            "서로의 필살기를 맞교환하는 찐팬 핏",
            "💡",
            "[매칭 스토리라인]",
            f"{na} 님은 '{my_want}'에 대한 결핍이 있고, "
            f"{nb} 님은 {ot_have} 등을 제공할 수 있는 전문가입니다. "
            f"반대로 {nb} 님은 '{ot_want}'를 원하며 {na} 님의 {my_have}가 맞닿습니다. "
            f"두 분 모두 '{my_val}' 철학과 '{my_dep}' 수준의 협업 온도가 맞아, "
            f"만나자마자 서로의 필살기를 깊이 주고받는 강력한 비즈니스 단골이 될 확률이 높습니다.",
        )

    if tier == "mid":
        return (
            "주니어가 성장하고, 시니어가 리프레시하는 멘토링 핏",
            "💡",
            "[매칭 스토리라인]",
            f"연차 {my_yrs}인 {na} 님은 '{my_dep}' 수준의 피드백을 원하고, "
            f"{nb} 님은 연차 {ot_yrs}의 {ot_job} 전문가입니다. "
            f"가치관이 '{my_val}'로 비슷해, "
            f"선배 대표가 후배 대표의 서비스 첫인상을 세심하게 짚어주는 "
            f"멘토-멘티형 단골 관계가 형성될 수 있습니다.",
        )

    if tier == "caution":
        return (
            "가치 온도 차이 — 내용 재확인 권장",
            "⚠️",
            "[주의 가이드]",
            f"{nb} 님이 원하는 깊이는 '{ot_dep}'인데, "
            f"{na} 님이 기대하는 협업 수준은 '{my_dep}'입니다. "
            f"Want↔Have 적합도({breakdown.get('want_have', 0)}%)와 깊이({breakdown.get('depth', 0)}%)를 "
            f"함께 보고 주관식 상세 내용을 한 번 더 검토해 주세요.",
        )

    return (
        "가치 균형 붕괴 (매칭 비추천)",
        "⚠️",
        "[주의 가이드]",
        f"상대방이 원하는 해결 깊이('{ot_dep}')와 {na} 님이 내어줄 가치 수준('{my_dep}')의 "
        f"무게감 차이가 큽니다. Want↔Have 교차 적합도도 {breakdown.get('want_have', 0)}%로 "
        f"낮아, 매칭 시 한쪽이 불만을 가질 수 있습니다. 주관식을 꼼꼼히 읽어보세요.",
    )


def _tier_from_pct(pct: int, depth_pts: int, want_pts: int) -> str:
    if pct >= 90:
        return "high"
    if pct >= 70:
        return "mid"
    if pct <= 50 or depth_pts <= 0 or want_pts < 40:
        return "low"
    return "caution"


def compute_value_match(me: pd.Series, other: pd.Series) -> ValueMatchResult:
    wh, mutual_wh = _want_have_component(me, other)
    dep = _depth_component(me, other)
    val = _values_component(me, other)
    loc = _locale_component(me, other)

    breakdown = {
        "want_have": wh,
        "depth": dep,
        "values": val,
        "locale": loc,
    }
    raw = (
        WEIGHTS["want_have"] * wh
        + WEIGHTS["depth"] * dep
        + WEIGHTS["values"] * val
        + WEIGHTS["locale"] * loc
    )
    pct = int(round(raw))

    tier = _tier_from_pct(pct, dep, wh)
    tier_title, icon, guide, story = _story_for_tier(tier, me, other, breakdown)

    return ValueMatchResult(
        pct=pct,
        tier=tier,
        tier_title=tier_title,
        guide_icon=icon,
        guide_label=guide,
        story=story,
        breakdown=breakdown,
        mutual_want_have=mutual_wh,
    )


def pct_badge_class(tier: str) -> str:
    return {"high": "value-high", "mid": "value-mid", "caution": "value-caution", "low": "value-low"}.get(
        tier, "value-mid"
    )


def breakdown_html(b: dict[str, int]) -> str:
    labels = {
        "want_have": "Want↔Have",
        "depth": "협업깊이",
        "values": "가치관",
        "locale": "지역·성별",
    }
    parts = [
        f'<span class="bd-item"><b>{labels[k]}</b> {v}%</span>'
        for k, v in b.items()
    ]
    return f'<div class="value-breakdown">{"".join(parts)}</div>'


def story_block_html(vm: ValueMatchResult, rank: int | None = None) -> str:
    import html as html_lib

    badge_cls = pct_badge_class(vm.tier)
    rank_html = (
        f'<span class="story-rank">추천 {rank}순위</span>' if rank else ""
    )
    story = html_lib.escape(vm.story)
    title = html_lib.escape(vm.tier_title)
    guide = html_lib.escape(vm.guide_label)
    return (
        f'<div class="story-block {badge_cls}">'
        f'<div class="story-head">{rank_html}'
        f'<span class="story-tier">{guide}</span>'
        f'<span class="story-title">{title}</span></div>'
        f'<p class="story-body">{story}</p>'
        f'{breakdown_html(vm.breakdown)}</div>'
    )


def value_badge_html(vm: ValueMatchResult) -> str:
    cls = pct_badge_class(vm.tier)
    return f'<span class="value-badge {cls}">가치 매칭 {vm.pct}%</span>'
