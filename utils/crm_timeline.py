"""신청자 타임라인 — CRM 신청자 탭."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from utils.columns import parse_checkbox, parse_reject
from utils.crm_truth import STAGE_LABELS, applicant_stage, is_matched_row


@dataclass(frozen=True)
class TimelineEvent:
    sort_key: str
    at: str
    label: str
    detail: str
    kind: str


def build_applicant_timeline(row: pd.Series) -> list[TimelineEvent]:
    """신청 → 입금 → 거절 → 매칭 → 환불 순 타임라인."""
    name = str(row.get("name", "")).strip()
    if not name:
        return []

    events: list[TimelineEvent] = []
    ts = str(row.get("ts", "") or "").strip()
    if ts:
        events.append(TimelineEvent(ts, ts, "신청 접수", "구글 폼 제출", "apply"))

    if parse_checkbox(row.get("paid", False)):
        events.append(
            TimelineEvent(
                ts or "9",
                ts or "—",
                "입금 확인",
                "V열 입금 체크",
                "paid",
            )
        )

    reject_n = parse_reject(row.get("reject", 0))
    if reject_n >= 1:
        events.append(
            TimelineEvent(
                "8",
                "—",
                "1차 거절",
                "재매칭 대상",
                "reject",
            )
        )
    if reject_n >= 2:
        events.append(
            TimelineEvent(
                "7",
                "—",
                "2차 거절",
                STAGE_LABELS["closed"],
                "closed",
            )
        )

    if is_matched_row(row):
        ma = str(row.get("matched_at", "") or "").strip()
        partner = str(row.get("matched_w", "") or "").strip()
        detail = f"상대: {partner}" if partner else "매칭 파트너 기록"
        events.append(
            TimelineEvent(
                ma or "6",
                ma or "—",
                "매칭 완료",
                detail,
                "matched",
            )
        )

    if parse_checkbox(row.get("refund", False)):
        events.append(
            TimelineEvent(
                "5",
                "—",
                "환불 처리",
                "환불 규정 적용",
                "refund",
            )
        )

    stage = applicant_stage(row)
    stage_label = STAGE_LABELS.get(stage, stage)
    events.append(
        TimelineEvent(
            "0",
            "현재",
            f"현재 · {stage_label}",
            "",
            "current",
        )
    )

    events.sort(key=lambda e: e.sort_key, reverse=True)
    return events
