"""CRM 오늘 할 일 큐 테스트."""
from datetime import datetime, timedelta, timezone

import pandas as pd

from utils.crm_queue import build_today_queue
from utils.sheets import load_demo_data


def test_build_today_queue_demo_has_unpaid():
    df = load_demo_data()
    items = build_today_queue(df)
    keys = [i.key for i in items]
    assert "unpaid" in keys
    unpaid = next(i for i in items if i.key == "unpaid")
    assert unpaid.count >= 1
    assert unpaid.priority <= 2


def test_build_today_queue_empty():
    df = pd.DataFrame(columns=["name", "paid", "refund", "matched", "reject", "ts"])
    assert build_today_queue(df) == []


def test_build_today_queue_sla_urgent():
    old = (datetime.now(timezone.utc) - timedelta(hours=72)).isoformat()
    df = pd.DataFrame(
        [{"name": "Late", "paid": False, "refund": False, "matched": "", "reject": 0, "ts": old}]
    )
    items = build_today_queue(df)
    assert len(items) == 1
    assert items[0].urgent is True
    assert items[0].sla_over == 1
    assert items[0].priority == 0
