"""프로필 상세 패널 — 시트 전 필드 가독성 렌더."""
from __future__ import annotations

import html as html_lib
import re
from typing import Callable

import pandas as pd

from utils.columns import format_matched_at, parse_checkbox, parse_reject
from utils.match_display import _theme

_URL_RE = re.compile(r"(https?://[^\s<>,\"']+)", re.IGNORECASE)

_LONG_KEYS = frozenset({
    "want", "have", "note", "have_action", "have_where",
    "product", "pain_today", "worth_it", "portfolio", "buyer_intent",
})

_PROFILE_SECTIONS: tuple[tuple[str, str, tuple[tuple[str, str], ...]], ...] = (
    (
        "신청 정보",
        "",
        (("ts", "신청 일시"),),
    ),
    (
        "나에 대해",
        "",
        (
            ("job", "직군"),
            ("region", "활동 지역"),
            ("years", "연차·전문성"),
            ("product", "운영·준비 중 아이템"),
        ),
    ),
    (
        "매칭 희망 조건",
        "",
        (
            ("w_job", "희망 직군"),
            ("w_region", "희망 지역"),
            ("w_gender", "희망 성별"),
            ("w_years", "희망 연차"),
            ("depth", "협업 깊이"),
            ("values", "가치관"),
        ),
    ),
    (
        "원하는 것 · 고민",
        "",
        (
            ("want", "답답한 부분"),
            ("pain_today", "당장 골치 아픈 문제"),
            ("worth_it", "5만원이 아깝지 않을 모습"),
        ),
    ),
    (
        "제공 가치",
        "have",
        (
            ("have", "비즈니스 자산"),
            ("have_action", "제공 행동(알맹이)"),
            ("have_where", "필요 자료·만남 방식"),
        ),
    ),
    (
        "참고 · 기타",
        "",
        (
            ("note", "추가 메모"),
            ("portfolio", "포트폴리오·링크"),
            ("buyer_intent", "바이어 목적 여부"),
        ),
    ),
    (
        "관리 · 동의",
        "admin",
        (
            ("paid_self", "참가비 입금(신청자)"),
            ("agree_refund", "환불 규칙 동의"),
            ("agree_privacy", "개인정보 동의"),
            ("refund_acct", "환불 계좌"),
            ("dday", "D-day"),
            ("reject", "매칭 횟수"),
            ("matched", "매칭 여부"),
            ("matched_w", "매칭 상대"),
            ("matched_at", "매칭일"),
            ("paid", "입금확인(관리자)"),
            ("refund", "환불 여부"),
        ),
    ),
)


def _empty(val) -> bool:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return True
    s = str(val).strip()
    return not s or s.lower() in ("nan", "none", "#ref!", "#n/a")


def _linkify(text: str) -> str:
    parts: list[str] = []
    last = 0
    for m in _URL_RE.finditer(text):
        parts.append(html_lib.escape(text[last : m.start()]))
        url = m.group(1).rstrip(".,;)")
        parts.append(
            f'<a class="profile-link" href="{html_lib.escape(url)}" '
            f'target="_blank" rel="noopener noreferrer">{html_lib.escape(url)}</a>'
        )
        last = m.end()
    parts.append(html_lib.escape(text[last:]))
    return "".join(parts)


def _short_job(j: str) -> str:
    return str(j or "").split("/")[0].strip()


def _short_years(y: str) -> str:
    return str(y or "").replace("연차 ", "")


def format_profile_value(key: str, val, *, format_dday: Callable[[object], str]) -> str:
    if key == "dday":
        s = format_dday(val)
        return html_lib.escape(s) if s else "—"
    if key in ("paid", "refund"):
        return "예" if parse_checkbox(val) else "아니오"
    if key == "reject":
        n = parse_reject(val)
        return str(n) if n else "0"
    if key == "matched":
        return "완료" if str(val or "").strip().upper() == "TRUE" else "—"
    if key == "matched_at":
        s = format_matched_at(val)
        return html_lib.escape(s) if s else "—"
    if _empty(val):
        if key in ("w_region", "w_gender", "w_years") and not val:
            return "무관"
        return "—"

    raw = str(val).strip()
    if key in ("job", "w_job"):
        return html_lib.escape(_short_job(raw))
    if key == "years":
        return html_lib.escape(_short_years(raw))
    if key in ("depth", "values"):
        return html_lib.escape(_theme(raw))
    if key == "portfolio" and _URL_RE.search(raw):
        return _linkify(raw)
    return html_lib.escape(raw)


def _meta_item(label: str, value_html: str, *, long: bool = False) -> str:
    cls = "meta-item meta-item-long" if long else "meta-item"
    val_cls = "meta-val meta-val-long" if long else "meta-val"
    empty_cls = " is-empty" if value_html == "—" else ""
    return (
        f'<div class="{cls}">'
        f'<span class="meta-lbl">{html_lib.escape(label)}</span>'
        f'<span class="{val_cls}{empty_cls}">{value_html}</span></div>'
    )


def _section_html(
    title: str,
    variant: str,
    fields: tuple[tuple[str, str], ...],
    row,
    *,
    format_dday: Callable[[object], str],
) -> str:
    short_bits: list[str] = []
    long_bits: list[str] = []
    for key, label in fields:
        val_html = format_profile_value(key, row.get(key, ""), format_dday=format_dday)
        if key in _LONG_KEYS:
            long_bits.append(_meta_item(label, val_html, long=True))
        else:
            short_bits.append(_meta_item(label, val_html))

    if not short_bits and not long_bits:
        return ""

    extra = f" {variant}" if variant else ""
    body = ""
    if short_bits:
        body += f'<div class="meta-grid">{"".join(short_bits)}</div>'
    if long_bits:
        body += f'<div class="profile-long-stack">{"".join(long_bits)}</div>'
    return (
        f'<div class="section-card{extra}">'
        f'<div class="section-title"><span class="ico">■</span> {html_lib.escape(title)}</div>'
        f"{body}</div>"
    )


def profile_sections_html(row, *, format_dday: Callable[[object], str]) -> str:
    return "".join(
        _section_html(title, variant, fields, row, format_dday=format_dday)
        for title, variant, fields in _PROFILE_SECTIONS
    )


def profile_hero_html(
    row,
    *,
    format_dday: Callable[[object], str],
    status_chip_html: str,
    fmt_contact: Callable[[object], str],
) -> str:
    dday_raw = format_dday(row.get("dday", ""))
    dday = html_lib.escape(dday_raw)
    contact = html_lib.escape(fmt_contact(row.get("contact", "")))
    extra_chips = ""
    if str(row.get("matched", "")).strip().upper() == "TRUE":
        ma = format_matched_at(row.get("matched_at"))
        if ma:
            extra_chips += f'<span class="chip chip-date">{html_lib.escape(ma)}</span>'
        partner = str(row.get("matched_w", "")).strip()
        if partner:
            extra_chips += f'<span class="chip chip-g">↔ {html_lib.escape(partner)}</span>'
    chips = (
        f'<div class="profile-chips">{status_chip_html}{extra_chips}'
        f'<span class="chip">{html_lib.escape(str(row.get("gender", "")))}</span>'
        f'<span class="chip">{html_lib.escape(str(row.get("region", "")))}</span>'
        f'<span class="chip">{html_lib.escape(_short_job(str(row.get("job", ""))))}</span>'
        f'<span class="chip">{html_lib.escape(_short_years(str(row.get("years", ""))))}</span>'
        f"</div>"
    )
    dday_badge = f'<span class="dday-badge">{dday}</span>' if dday_raw else ""
    return (
        f'<div class="profile-hero">'
        f'<div class="profile-top">'
        f'<div><h2 class="profile-name">{html_lib.escape(str(row.get("name", "")))}</h2>'
        f'<div class="profile-contact">{contact}</div></div>'
        f'{dday_badge}</div>'
        f"{chips}</div>"
    )
