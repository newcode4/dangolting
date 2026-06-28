"""신청자 타임라인 테스트."""
import pandas as pd

from utils.crm_timeline import build_applicant_timeline


def test_timeline_apply_only():
    row = pd.Series({"name": "A", "ts": "2026. 6. 26", "paid": False, "refund": False, "matched": "", "reject": 0})
    events = build_applicant_timeline(row)
    labels = [e.label for e in events]
    assert "신청 접수" in labels
    assert "현재 · 입금 대기" in labels


def test_timeline_matched():
    row = pd.Series({
        "name": "A", "ts": "2026. 6. 26", "paid": True, "refund": False,
        "matched": "TRUE", "matched_w": "B", "matched_at": "2026. 6. 28", "reject": 0,
    })
    events = build_applicant_timeline(row)
    labels = [e.label for e in events]
    assert "매칭 완료" in labels
    assert any("B" in e.detail for e in events)
