"""CRM Single Source of Truth — 상태·매출·단계·시트 정합성."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone

import pandas as pd

from utils.columns import parse_checkbox, parse_reject
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

DEFAULT_SLA_UNPAID_HOURS = 48


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


@dataclass(frozen=True)
class RevenueSnapshot:
    paid_count: int
    refund_count: int
    fee: int
    revenue_paid: int
    revenue_refunded: int


@dataclass(frozen=True)
class SheetAnomaly:
    row_index: int
    name: str
    code: str
    message: str


def fee_amount() -> int:
    digits = "".join(c for c in PARTICIPATION_FEE if c.isdigit())
    return int(digits) if digits else 0


def count_by_stage(df: pd.DataFrame) -> dict[str, int]:
    """시트 행 → stage_key 집계. name 비어 있으면 invalid(미집계)."""
    counts = {k: 0 for k in STAGE_LABELS}
    if df.empty:
        return counts
    for _, row in df.iterrows():
        stage = applicant_stage(row)
        if stage in counts:
            counts[stage] += 1
    return counts


def paid_applicant_count(df: pd.DataFrame) -> int:
    """입금 ✅ · 환불 제외 · 성함 있는 행."""
    if df.empty:
        return 0
    n = 0
    for _, row in df.iterrows():
        if not str(row.get("name", "")).strip():
            continue
        if parse_checkbox(row.get("paid", False)) and not parse_checkbox(row.get("refund", False)):
            n += 1
    return n


def revenue_metrics(df: pd.DataFrame) -> RevenueSnapshot:
    """매출 = 입금 확인(환불 제외) × 참가비 / 환불 건 × 참가비."""
    counts = count_by_stage(df)
    fee = fee_amount()
    refund_count = counts.get("refunded", 0)
    paid_count = paid_applicant_count(df)
    return RevenueSnapshot(
        paid_count=paid_count,
        refund_count=refund_count,
        fee=fee,
        revenue_paid=paid_count * fee,
        revenue_refunded=refund_count * fee,
    )


def filter_unpaid_rows(df: pd.DataFrame) -> pd.DataFrame:
    """입금 대기 — applicant_stage == unpaid."""
    if df.empty:
        return df
    mask = df.apply(lambda r: applicant_stage(r) == "unpaid", axis=1)
    return df[mask].sort_index()


def _applied_at_utc(val: date | datetime) -> datetime:
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=timezone.utc)
        return val.astimezone(timezone.utc)
    return datetime.combine(val, datetime.min.time(), tzinfo=timezone.utc)


def unpaid_sla_over_count(df: pd.DataFrame, *, sla_hours: int = DEFAULT_SLA_UNPAID_HOURS) -> int:
    """신청 후 SLA 시간 초과 입금 대기 건수."""
    if df.empty:
        return 0
    now = datetime.now(timezone.utc)
    n = 0
    for _, row in filter_unpaid_rows(df).iterrows():
        applied = parse_ts(row.get("ts", ""))
        if applied is None:
            continue
        hours = (now - _applied_at_utc(applied)).total_seconds() / 3600
        if hours >= sla_hours:
            n += 1
    return n


def detect_sheet_anomalies(df: pd.DataFrame) -> list[SheetAnomaly]:
    """시트 수기 입력 불일치."""
    if df.empty:
        return []
    out: list[SheetAnomaly] = []
    for idx, row in df.iterrows():
        name = str(row.get("name", "")).strip()
        if not name:
            continue
        paid = parse_checkbox(row.get("paid", False))
        refund = parse_checkbox(row.get("refund", False))
        matched = is_matched_row(row)
        reject_n = parse_reject(row.get("reject", 0))
        row_i = int(idx)

        if paid and refund:
            out.append(
                SheetAnomaly(row_i, name, "paid_and_refund", "입금·환불 동시 체크")
            )
        if matched and reject_n >= 2:
            out.append(
                SheetAnomaly(row_i, name, "matched_and_closed", "매칭 완료 + 거절 2회")
            )
        if matched and not str(row.get("matched_at", "") or "").strip():
            out.append(
                SheetAnomaly(row_i, name, "matched_no_date", "매칭 TRUE · 매칭일 없음")
            )
    return out


def stage_labels_for_keys(*keys: str) -> list[str]:
    return [STAGE_LABELS[k] for k in keys if k in STAGE_LABELS]
