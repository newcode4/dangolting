"""CRM 오늘 할 일 큐 — 우선순위·SLA."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from utils.crm_truth import (
    DEFAULT_SLA_UNPAID_HOURS,
    count_by_stage,
    unpaid_sla_over_count,
)


@dataclass(frozen=True)
class QueueItem:
    key: str
    title: str
    count: int
    sla_over: int
    priority: int
    stage_keys: tuple[str, ...]
    hint: str
    color: str
    urgent: bool


def build_today_queue(
    df: pd.DataFrame,
    *,
    sla_hours: int = DEFAULT_SLA_UNPAID_HOURS,
) -> list[QueueItem]:
    """처리 우선순위 큐. count=0 인 항목 제외."""
    counts = count_by_stage(df)
    sla_over = unpaid_sla_over_count(df, sla_hours=sla_hours)
    items: list[QueueItem] = []

    unpaid_n = counts.get("unpaid", 0)
    if unpaid_n:
        items.append(
            QueueItem(
                key="unpaid",
                title="입금 대기",
                count=unpaid_n,
                sla_over=sla_over,
                priority=0 if sla_over else 1,
                stage_keys=("unpaid",),
                hint=f"미입금 {unpaid_n}명" + (f" · {sla_over}명 {sla_hours}h+" if sla_over else ""),
                color="#d29922",
                urgent=sla_over > 0,
            )
        )

    reject_n = counts.get("reject_1", 0)
    if reject_n:
        items.append(
            QueueItem(
                key="reject_1",
                title="1차 거절 · 재매칭",
                count=reject_n,
                sla_over=0,
                priority=2,
                stage_keys=("reject_1",),
                hint=f"재매칭 필요 {reject_n}명",
                color="#a371f7",
                urgent=False,
            )
        )

    matching_n = counts.get("matching", 0)
    if matching_n:
        items.append(
            QueueItem(
                key="matching",
                title="매칭 진행",
                count=matching_n,
                sla_over=0,
                priority=3,
                stage_keys=("matching",),
                hint=f"연결 진행 중 {matching_n}명",
                color="#58a6ff",
                urgent=False,
            )
        )

    items.sort(key=lambda x: (x.priority, -x.count))
    return items
