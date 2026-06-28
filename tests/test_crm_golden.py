"""CRM golden snapshot — demo 데이터 고정 회귀."""
from utils.crm import build_crm_snapshot
from utils.crm_events import demo_events
from utils.crm_truth import count_by_stage, revenue_metrics
from utils.demo_data import DEMO_DATA
from utils.sheets import load_demo_data


def test_golden_stage_counts():
    df = load_demo_data()
    counts = count_by_stage(df)
    assert counts["unpaid"] == 1
    assert counts["matching"] == 3
    assert counts["reject_1"] == 1
    assert counts["matched"] == 1
    assert counts["closed"] == 1
    assert counts["refunded"] == 1
    assert sum(counts.values()) == len(DEMO_DATA)


def test_golden_revenue():
    df = load_demo_data()
    rev = revenue_metrics(df)
    assert rev.fee == 50000
    assert rev.paid_count == 6
    assert rev.refund_count == 1
    assert rev.revenue_paid == 300_000
    assert rev.revenue_refunded == 50_000


def test_golden_snapshot_funnel_keys():
    df = load_demo_data()
    snap = build_crm_snapshot(df, events=demo_events())
    keys = [s.key for s in snap.funnel]
    assert keys == [
        "visit_u", "visit_t", "apply_u", "apply_t", "form",
        "paid", "unpaid", "matching_pool", "matched", "refunded",
    ]
    assert snap.form_total == len(DEMO_DATA)
    assert snap.revenue_paid == 300_000
    assert snap.revenue_refunded == 50_000


def test_golden_event_totals():
    snap = build_crm_snapshot(load_demo_data(), events=demo_events())
    assert snap.event_summary["unique"]["page_view"] >= 1
    assert snap.event_summary["totals"]["apply_click"] >= 1
