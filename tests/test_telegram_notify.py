"""텔레그램 신규 신청 메시지 포맷·감지."""
from __future__ import annotations

from unittest.mock import patch

import pandas as pd

from utils.telegram_notify import format_applicant_message, process_new_applicants


def test_format_applicant_message():
    row = pd.Series(
        {
            "name": "이주환",
            "contact": "01045678978",
            "job": "전문 컨설턴트 / 강사",
            "region": "경기도",
            "ts": "2026. 6. 26 오후 8:07:14",
            "paid": False,
        }
    )
    msg = format_applicant_message(row)
    assert "이주환" in msg
    assert "01045678978" in msg
    assert "전문 컨설턴트" in msg
    assert "경기도" in msg
    assert "2026" in msg
    assert "입금 대기" in msg
    assert "🆕" in msg


def test_format_applicant_message_empty_fields_show_dash():
    row = pd.Series({"name": "홍길동", "job": "", "region": "", "ts": "", "paid": True})
    msg = format_applicant_message(row)
    assert "이름: 홍길동" in msg
    assert "직군: —" in msg
    assert "입금 확인" in msg


def test_process_new_applicants_notifies_unpaid_row():
    """입금 대기(paid=False) 신규 행도 알림 대상."""
    df = pd.DataFrame(
        [{"name": "신규", "job": "창업", "region": "서울", "ts": "now", "paid": False}],
        index=[5],
    )
    sent: list[int] = []

    def fake_send(_text: str) -> bool:
        sent.append(1)
        return True

    with patch("utils.telegram_notify.telegram_enabled", return_value=True), patch(
        "utils.telegram_notify.send_telegram", side_effect=fake_send
    ), patch("utils.telegram_notify.load_last_notified_row", return_value=4), patch(
        "utils.telegram_notify.save_last_notified_row"
    ):
        n = process_new_applicants(df, "http://sheet", "ws")
    assert n == 1
    assert len(sent) == 1