"""CRM 퍼널 · 단계 분류 테스트."""
import pandas as pd

from utils.crm import applicant_stage, build_crm_snapshot
from utils.crm_events import demo_events, record_event, summarize_events
from utils.demo_data import DEMO_DATA
from utils.sheets import load_demo_data


def test_applicant_stage_unpaid():
    row = pd.Series({"name": "A", "paid": False, "refund": False, "matched": "", "reject": 0})
    assert applicant_stage(row) == "unpaid"


def test_applicant_stage_matched():
    row = pd.Series({"name": "A", "paid": True, "refund": False, "matched": "TRUE", "reject": 0})
    assert applicant_stage(row) == "matched"


def test_applicant_stage_refund_priority():
    row = pd.Series({"name": "A", "paid": True, "refund": True, "matched": "TRUE", "reject": 0})
    assert applicant_stage(row) == "refunded"


def test_applicant_stage_closed():
    row = pd.Series({"name": "A", "paid": True, "refund": False, "matched": "", "reject": 2})
    assert applicant_stage(row) == "closed"


def test_build_crm_snapshot_demo():
    df = load_demo_data()
    snap = build_crm_snapshot(df, events=demo_events())
    assert snap.form_total == len(DEMO_DATA)
    assert snap.stage_counts["unpaid"] >= 1
    assert snap.stage_counts["matched"] >= 1
    assert snap.stage_counts["refunded"] >= 1
    assert snap.event_summary["unique"]["page_view"] >= 1
    assert any(s.key == "form" for s in snap.funnel)


def test_record_and_summarize_events(tmp_path, monkeypatch):
    from utils import crm_events as mod

    path = tmp_path / "crm_events.jsonl"
    monkeypatch.setattr(mod, "EVENTS_PATH", path)
    record_event("page_view", visitor_id="u1")
    record_event("apply_click", visitor_id="u1")
    record_event("page_view", visitor_id="u2")
    summary = summarize_events(mod.load_events())
    assert summary["totals"]["page_view"] == 2
    assert summary["unique"]["apply_click"] == 1
