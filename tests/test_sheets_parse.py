"""헤더 행 기반 열 매핑."""
from __future__ import annotations

import pandas as pd

from utils.columns import build_column_map, normalize_dataframe
from utils.sheets import records_from_sheet_values
from utils.unpaid import unpaid_applicants


def test_records_from_sheet_values_ignores_header_labels():
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
    df = normalize_dataframe(pd.DataFrame(records), apply_eligibility=False)
    assert df.loc[0, "name"] == "홍길동"
    assert df.loc[0, "job"] == "마케터"
    assert df.loc[0, "region"] == "서울특별시"
    assert "2026" in str(df.loc[0, "ts"])


def test_header_map_finds_name_column():
    headers = ["타임스탬프", "이름", "성별", "연락처", "메인직군", "거주/활동지역"]
    m = build_column_map(headers)
    assert m["name"] == 1
    assert m["job"] == 4
    assert m["region"] == 5


def test_header_map_extra_email_column():
    """이메일 열이 끼면 고정 열 번호만으로는 깨짐 → 헤더 매칭으로 복구."""
    all_values = [
        ["타임스탬프", "이름", "이메일", "연락처", "메인 직군", "거주/활동지역"],
        ["2026.1.1", "김기자", "a@b.com", "010", "기자", "서울"],
    ]
    df = normalize_dataframe(pd.DataFrame(records_from_sheet_values(all_values)), apply_eligibility=False)
    assert df.loc[0, "name"] == "김기자"
    assert df.loc[0, "job"] == "기자"
    assert df.loc[0, "region"] == "서울"


def test_unpaid_applicants():
    df = pd.DataFrame(
        [
            {"name": "A", "paid": True, "refund": False},
            {"name": "B", "paid": False, "refund": False},
        ],
        index=[2, 3],
    )
    out = unpaid_applicants(df)
    assert len(out) == 1
    assert out.loc[3, "name"] == "B"
