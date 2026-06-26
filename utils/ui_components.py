"""UI HTML 컴포넌트 — 목업 디자인"""
from __future__ import annotations

import html as html_lib

from utils.value_match import ValueMatchResult, pct_badge_class


def value_fit_badge(vm: ValueMatchResult) -> str:
    cls = pct_badge_class(vm.tier)
    return f'<span class="fit-badge {cls}">가치 적합 {vm.pct}%</span>'


def progress_bars_html(breakdown: dict[str, int]) -> str:
    labels = {
        "want_have": "Want↔Have",
        "depth": "협업깊이",
        "values": "가치관",
        "locale": "지역·성별",
    }
    rows = []
    for key, val in breakdown.items():
        tone = "fill-hi" if val >= 70 else "fill-md" if val >= 40 else "fill-lo"
        rows.append(
            f'<div class="prog-row">'
            f'<span class="prog-lbl">{labels.get(key, key)}</span>'
            f'<div class="prog-track"><div class="prog-fill {tone}" style="width:{val}%"></div></div>'
            f'<span class="prog-pct">{val}%</span></div>'
        )
    return f'<div class="prog-block">{"".join(rows)}</div>'


def recommendation_card_html(
    name: str,
    vm: ValueMatchResult,
    rank: int,
    kw_row_html: str,
    meta_html: str = "",
) -> str:
    nm = html_lib.escape(name)
    title = html_lib.escape(vm.tier_title)
    story = html_lib.escape(vm.story)
    guide = html_lib.escape(vm.guide_label)
    tier_cls = pct_badge_class(vm.tier)
    meta_block = f'<div class="rec-meta-row">{meta_html}</div>' if meta_html else ""
    return (
        f'<div class="mock-rec {tier_cls}">'
        f'<div class="mock-rec-head">'
        f'<div class="mock-rec-left">'
        f'<span class="mock-rec-rank">추천 {rank}순위</span>'
        f'<span class="mock-rec-name">{nm}</span></div>'
        f'{value_fit_badge(vm)}</div>'
        f'<div class="mock-rec-tags">'
        f'<span class="logic-tag">{guide}</span>'
        f'<span class="logic-tag logic-blue">가치 관점 분석</span>'
        f'<span class="logic-tag logic-muted">{title}</span></div>'
        f'<p class="mock-rec-story">{story}</p>'
        f'{progress_bars_html(vm.breakdown)}'
        f'<div class="mock-rec-kw">{kw_row_html}</div>'
        f"{meta_block}</div>"
    )
