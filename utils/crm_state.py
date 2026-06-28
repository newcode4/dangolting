"""CRM 상태 머신 — 허용 전이 검증."""
from __future__ import annotations

import pandas as pd

from utils.columns import parse_checkbox, parse_reject
from utils.crm_truth import STAGE_LABELS, applicant_stage, is_matched_row

# stage_key → 허용되는 다음 stage_key
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "invalid": {"unpaid"},
    "unpaid": {"matching", "refunded"},
    "matching": {"matched", "reject_1", "closed", "refunded"},
    "reject_1": {"matched", "closed", "refunded"},
    "matched": {"refunded"},
    "closed": {"refunded"},
    "refunded": set(),
}


def can_transition(from_stage: str, to_stage: str) -> bool:
    if from_stage == to_stage:
        return True
    return to_stage in ALLOWED_TRANSITIONS.get(from_stage, set())


def _row_with_field(row: pd.Series, field: str, new_value: object) -> pd.Series:
    trial = row.copy()
    trial[field] = new_value
    return trial


def stage_after_change(row: pd.Series, field: str, new_value: object) -> str:
    return applicant_stage(_row_with_field(row, field, new_value))


def validate_row_transition(row: pd.Series, field: str, new_value: object) -> str | None:
    """전이 불가 시 한국어 에러 메시지, 가능하면 None."""
    current = applicant_stage(row)
    if current == "invalid":
        return "성함이 없는 행은 처리할 수 없습니다."

    next_stage = stage_after_change(row, field, new_value)
    if current == next_stage:
        return None
    if can_transition(current, next_stage):
        return None

    cur_label = STAGE_LABELS.get(current, current)
    next_label = STAGE_LABELS.get(next_stage, next_stage)
    return f"「{cur_label}」 상태에서는 「{next_label}」로 변경할 수 없습니다."


def validate_match(row: pd.Series) -> str | None:
    if parse_checkbox(row.get("refund", False)):
        return "환불 처리된 신청자는 매칭할 수 없습니다."
    if is_matched_row(row):
        return "이미 매칭 완료된 신청자입니다."
    if parse_reject(row.get("reject", 0)) >= 2:
        return "거절 2회로 종료된 신청자입니다."
    if not parse_checkbox(row.get("paid", False)):
        return "입금 확인 후에만 매칭할 수 있습니다."
    return validate_row_transition(row, "matched", "TRUE")


def validate_reject_increment(row: pd.Series) -> str | None:
    cur = parse_reject(row.get("reject", 0))
    if cur >= 2:
        return "거절 횟수가 이미 최대(2회)입니다."
    if parse_checkbox(row.get("refund", False)):
        return "환불 처리된 신청자는 거절할 수 없습니다."
    if is_matched_row(row):
        return "매칭 완료된 신청자는 거절할 수 없습니다."
    if not parse_checkbox(row.get("paid", False)):
        return "입금 확인 후에만 거절 처리할 수 있습니다."
    return validate_row_transition(row, "reject", cur + 1)
