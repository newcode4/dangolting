"""시트 열 위치 기반 파싱 — 폼 헤더 문구와 무관."""
from __future__ import annotations

import pandas as pd

from utils.sheets import records_from_sheet_values
from utils.columns import normalize_dataframe


def test_records_from_sheet_values_ignores_header_labels():
    """헤더가 '타임스탬프'·'메인 직군'이어도 E/F/A열 값을 읽는다."""
    all_values = [
        ["타임스탬프", "성함", "성별", "연락처", "메인 직군", "거주/활동지역"],
        [
            "2026. 6. 27 오후 3:00:00",
            "홍길동",
            "남자",
            "01012345678",
            "마케터",
            "서울특별시",
        ],
    ]
    records = records_from_sheet_values(all_values)
    assert len(records) == 1
    df = normalize_dataframe(pd.DataFrame(records), apply_eligibility=False)
    assert df.loc[0, "name"] == "홍길동"
    assert df.loc[0, "job"] == "마케터"
    assert df.loc[0, "region"] == "서울특별시"
    assert "2026" in str(df.loc[0, "ts"])
