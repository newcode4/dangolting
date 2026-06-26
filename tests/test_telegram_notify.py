"""텔레그램 신규 신청 메시지 포맷."""
from __future__ import annotations

import pandas as pd

from utils.telegram_notify import format_applicant_message


def test_format_applicant_message():
    row = pd.Series(
        {
            "name": "이주환",
            "job": "전문 컨설턴트 / 강사",
            "region": "경기도",
            "ts": "2026. 6. 26 오후 8:07:14",
            "paid": False,
        }
    )
    msg = format_applicant_message(row)
    assert "이주환" in msg
    assert "입금 대기" in msg
    assert "🆕" in msg
