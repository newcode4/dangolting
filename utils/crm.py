"""CRM 퍼널 — 시트 신청 데이터 + 랜딩 이벤트."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from utils.columns import parse_checkbox, parse_reject
from utils.crm_events import demo_events, load_events, summarize_events
from utils.date_filter import parse_ts
from utils.landing_config import PARTICIPATION_FEE

STAGE_LABELS: dict[str, str] = {
    "refunded": "환불",
    "matched": "매칭 완료",
    "closed": "종료(거절 2회)",
    "reject_1": "1차 거절 · 재매칭",
    "matching": "매칭 진행",
    "unpaid": "입금 대기",
    "invalid": "—",
}

STAGE_ORDER = (
    "unpaid",
    "matching",
    "reject_1",
    "matched",
    "closed",
    "refunded",
)


def is_matched_row(row: pd.Series) -> bool:
    return str(row.get("matched", "")).strip().upper() == "TRUE"


def applicant_stage(row: pd.Series) -> str:
    """신청자 1명의 CRM 파이프라인 단계."""
    name = str(row.get("name", "")).strip()
    if not name:
        return "invalid"

    if parse_checkbox(row.get("refund", False)):
        return "refunded"
    if is_matched_row(row):
        return "matched"

    reject_n = parse_reject(row.get("reject", 0))
    if reject_n >= 2:
        return "closed"
    if reject_n == 1:
        return "reject_1"
    if parse_checkbox(row.get("paid", False)):
        return "matching"
    return "unpaid"


def _pct(num: int, denom: int) -> float | None:
    if denom <= 0:
        return None
    return round(num / denom * 100, 1)


def _fee_amount() -> int:
    digits = "".join(c for c in PARTICIPATION_FEE if c.isdigit())
    return int(digits) if digits else 0


@dataclass
class FunnelStep:
    key: str
    label: str
    count: int
    unique: int | None = None
    rate_from_prev: float | None = None
    rate_from_top: float | None = None
    hint: str = ""


@dataclass
class CrmSnapshot:
    funnel: list[FunnelStep] = field(default_factory=list)
    stage_counts: dict[str, int] = field(default_factory=dict)
    applicants: list[dict[str, Any]] = field(default_factory=list)
    event_summary: dict[str, Any] = field(default_factory=dict)
    daily_applicants: dict[str, int] = field(default_factory=dict)
    revenue_paid: int = 0
    revenue_refunded: int = 0
    form_total: int = 0


def build_applicant_rows(raw: pd.DataFrame) -> list[dict[str, Any]]:
    if raw.empty:
        return []
    rows: list[dict[str, Any]] = []
    for idx, row in raw.iterrows():
        name = str(row.get("name", "")).strip()
        if not name:
            continue
        stage = applicant_stage(row)
        rows.append(
            {
                "행": int(idx),
                "신청일": str(row.get("ts", "") or "—"),
                "이름": name,
                "연락처": str(row.get("contact", "") or "—"),
                "직군": str(row.get("job", "") or "—")[:48],
                "지역": str(row.get("region", "") or "—"),
                "단계": STAGE_LABELS.get(stage, stage),
                "stage_key": stage,
                "입금": "✅" if parse_checkbox(row.get("paid", False)) else "—",
                "매칭": "✅" if is_matched_row(row) else "—",
                "거절": parse_reject(row.get("reject", 0)),
                "환불": "✅" if parse_checkbox(row.get("refund", False)) else "—",
                "D-day": str(row.get("dday", "") or "—"),
                "매칭일": str(row.get("matched_at", "") or "—"),
            }
        )
    rows.sort(key=lambda r: r.get("신청일", ""), reverse=True)
    return rows


def build_crm_snapshot(raw: pd.DataFrame, *, events: list[dict] | None = None) -> CrmSnapshot:
    ev = events if events is not None else load_events()
    ev_sum = summarize_events(ev)

    applicants = build_applicant_rows(raw)
    form_total = len(applicants)

    stage_counts = {k: 0 for k in STAGE_LABELS}
    for a in applicants:
        key = a.get("stage_key", "invalid")
        if key in stage_counts:
            stage_counts[key] += 1

    paid_n = sum(1 for a in applicants if a["입금"] == "✅" and a["환불"] != "✅")
    matched_n = stage_counts.get("matched", 0)
    refund_n = stage_counts.get("refunded", 0)
    unpaid_n = stage_counts.get("unpaid", 0)

    visits_u = ev_sum["unique"].get("page_view", 0)
    visits_t = ev_sum["totals"].get("page_view", 0)
    apply_u = ev_sum["unique"].get("apply_click", 0)
    apply_t = ev_sum["totals"].get("apply_click", 0)

    fee = _fee_amount()
    revenue_paid = paid_n * fee
    revenue_refunded = refund_n * fee

    daily_applicants: dict[str, int] = {}
    if not raw.empty and "ts" in raw.columns:
        for d in raw["ts"].map(parse_ts):
            if d is not None:
                key = d.isoformat()
                daily_applicants[key] = daily_applicants.get(key, 0) + 1

    steps: list[FunnelStep] = [
        FunnelStep(
            "visit_u",
            "랜딩 방문 (순)",
            visits_u,
            unique=visits_u,
            hint="고유 방문자 · localStorage ID 기준",
        ),
        FunnelStep(
            "visit_t",
            "랜딩 방문 (총)",
            visits_t,
            rate_from_prev=_pct(visits_t, visits_u or visits_t or 1),
            hint="페이지뷰 합계",
        ),
        FunnelStep(
            "apply_u",
            "참여 신청 클릭 (순)",
            apply_u,
            unique=apply_u,
            rate_from_prev=_pct(apply_u, visits_u),
            rate_from_top=_pct(apply_u, visits_u),
            hint="「지금 참여 신청하기」 클릭",
        ),
        FunnelStep(
            "apply_t",
            "참여 신청 클릭 (총)",
            apply_t,
            rate_from_prev=_pct(apply_t, apply_u or apply_t or 1),
            hint="CTA 클릭 합계",
        ),
        FunnelStep(
            "form",
            "폼 제출 (신청)",
            form_total,
            rate_from_prev=_pct(form_total, apply_u or apply_t),
            rate_from_top=_pct(form_total, visits_u),
            hint="구글 시트 신청 행 · 성함 있는 행",
        ),
        FunnelStep(
            "paid",
            "입금 확인",
            paid_n,
            rate_from_prev=_pct(paid_n, form_total),
            rate_from_top=_pct(paid_n, visits_u),
            hint="시트 V열 입금확인 · 환불 제외",
        ),
        FunnelStep(
            "matching_pool",
            "매칭 풀 (입금·진행)",
            stage_counts.get("matching", 0) + stage_counts.get("reject_1", 0),
            rate_from_prev=_pct(stage_counts.get("matching", 0) + stage_counts.get("reject_1", 0), paid_n),
            hint="입금 후 매칭 대기 + 1차 거절 재매칭",
        ),
        FunnelStep(
            "matched",
            "매칭 완료",
            matched_n,
            rate_from_prev=_pct(matched_n, paid_n),
            rate_from_top=_pct(matched_n, visits_u),
            hint="시트 X열 매칭 여부 TRUE",
        ),
        FunnelStep(
            "refunded",
            "환불",
            refund_n,
            rate_from_prev=_pct(refund_n, form_total),
            hint="시트 Y열 환불 여부",
        ),
    ]

    # 보조 지표 — 입금 대기
    steps.insert(
        6,
        FunnelStep(
            "unpaid",
            "입금 대기",
            unpaid_n,
            rate_from_prev=_pct(unpaid_n, form_total),
            hint="폼 제출 후 V열 미체크",
        ),
    )

    return CrmSnapshot(
        funnel=steps,
        stage_counts=stage_counts,
        applicants=applicants,
        event_summary=ev_sum,
        daily_applicants=dict(sorted(daily_applicants.items())),
        revenue_paid=revenue_paid,
        revenue_refunded=revenue_refunded,
        form_total=form_total,
    )


def crm_events_for_mode(*, demo_mode: bool) -> list[dict]:
    stored = load_events()
    if demo_mode and not stored:
        return demo_events()
    return stored
