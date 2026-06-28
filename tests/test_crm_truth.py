"""CRM Single Source of Truth 테스트."""
import pandas as pd

from utils.crm_truth import (
    count_by_stage,
    detect_sheet_anomalies,
    filter_unpaid_rows,
    revenue_metrics,
)
from utils.demo_data import DEMO_DATA
from utils.sheets import load_demo_data


def test_count_by_stage_matches_demo():
    df = load_demo_data()
    counts = count_by_stage(df)
    assert counts["unpaid"] >= 1
    assert counts["matched"] >= 1
    assert counts["refunded"] >= 1
    assert sum(counts.values()) == len(DEMO_DATA)


def test_revenue_metrics_demo():
    df = load_demo_data()
    rev = revenue_metrics(df)
    assert rev.fee == 50000
    assert rev.revenue_paid == rev.paid_count * 50000
    assert rev.revenue_refunded == rev.refund_count * 50000


def test_filter_unpaid_rows():
    df = pd.DataFrame(
        [
            {"name": "A", "paid": False, "refund": False, "matched": "", "reject": 0},
            {"name": "B", "paid": True, "refund": False, "matched": "", "reject": 0},
        ]
    )
    out = filter_unpaid_rows(df)
    assert len(out) == 1
    assert out.iloc[0]["name"] == "A"


def test_detect_sheet_anomalies_paid_and_refund():
    df = pd.DataFrame(
        [{"name": "X", "paid": True, "refund": True, "matched": "", "reject": 0}]
    )
    anomalies = detect_sheet_anomalies(df)
    assert len(anomalies) == 1
    assert anomalies[0].code == "paid_and_refund"


def test_detect_sheet_anomalies_matched_no_date():
    df = pd.DataFrame(
        [{"name": "Y", "paid": True, "refund": False, "matched": "TRUE", "reject": 0, "matched_at": ""}]
    )
    anomalies = detect_sheet_anomalies(df)
    assert any(a.code == "matched_no_date" for a in anomalies)
