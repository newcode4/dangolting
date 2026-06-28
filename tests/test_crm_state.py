"""CRM 상태 머신 테스트."""
import pandas as pd

from utils.crm_state import (
    can_transition,
    validate_match,
    validate_reject_increment,
    validate_row_transition,
)


def test_can_transition_unpaid_to_matching():
    assert can_transition("unpaid", "matching")
    assert not can_transition("unpaid", "matched")


def test_validate_match_requires_paid():
    row = pd.Series({"name": "A", "paid": False, "refund": False, "matched": "", "reject": 0})
    assert validate_match(row) == "입금 확인 후에만 매칭할 수 있습니다."


def test_validate_match_ok():
    row = pd.Series({"name": "A", "paid": True, "refund": False, "matched": "", "reject": 0})
    assert validate_match(row) is None


def test_validate_reject_from_matched_blocked():
    row = pd.Series({"name": "A", "paid": True, "refund": False, "matched": "TRUE", "reject": 0})
    assert validate_reject_increment(row) == "매칭 완료된 신청자는 거절할 수 없습니다."


def test_validate_reject_increment_ok():
    row = pd.Series({"name": "A", "paid": True, "refund": False, "matched": "", "reject": 0})
    assert validate_reject_increment(row) is None


def test_validate_row_transition_unmatch_blocked():
    row = pd.Series({"name": "A", "paid": True, "refund": False, "matched": "TRUE", "reject": 0})
    err = validate_row_transition(row, "matched", "FALSE")
    assert err is not None
    assert "변경할 수 없습니다" in err
