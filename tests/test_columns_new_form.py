"""2026-06 확장 폼 시트 헤더 매핑."""
from __future__ import annotations

import pandas as pd

from utils.columns import COL, build_column_map, normalize_dataframe
from utils.sheets import records_from_sheet_values

NEW_FORM_HEADERS = [
    "타임스탬프",
    "성함",
    "본인의 성별을 알려주세요.",
    "연락처",
    "나의 직군은 무엇인가요?",
    "주로 활동하시는 지역(위치)은 어디인가요?",
    "나의 현재 전문성 및 연차 체급은 어느 정도인가요?",
    "상대방에게 당장 제공할 수 있는 나의 '비즈니스 자산'은 무엇인가요?",
    "매칭 희망하는 지역",
    "매칭 성별 선호도",
    "찾으시는 상대방의 직군은 무엇인가요?",
    "상대방에게 기대하는 연차 무엇인가요?",
    "비즈니스를 하거나 내 일을 할 때, 내가 가장 중요하게 생각하는 가치는 무엇인가요?",
    "내가 상대방에게 바라는 문제 해결의 깊이는 어느 정도인가요?",
    "지금 내 사업에서 '가장 답답하고 막막한 부분'은 어디인가요?",
    "추가적으로 하고 싶은 말",
    "단골팅 참가비 입금을 완료하셨나요",
    "단골팅 환불 및 진행 규칙에 동의하십니까?",
    "개인정보 수집 및 이용 동의 하십니까?",
    "환불 받을 계좌를 알려주세요",
    "제공할 가치의 '정확한 알맹이(행동)'를 알려주세요.",
    "상대방이 '어떤 자료'를 들고 오거나, '어디로' 오면 그걸 해줄 수 있나요?",
    "지금 돈을 벌고 있거나, 준비 중인 '아이템/서비스'는 무엇인가요?",
    "그 아이템을 굴리면서 '오늘 당장 내 머리를 싸매게 만드는 가장 골치 아픈   문제'는 무엇인가요?",
    "상대방이 나에게 '이렇게까지 해주면 이번 단골팅 5만원이 전혀 아깝지 않겠다' 하는 구체적인 모습을 적어주세요.",
    "나의 전문성을 보여줄 수 있는 포트폴리오나 참고 링크가 있다면 남겨주세요. (없다면 '없음' 입력)",
    "단골팅은 서로 대등하게 돕는 '파트너십' 매칭입니다. 혹시 \"내 제품을 살 고객(바이어)을 찾고 싶다\"는 목적이신가요?",
    "20열",
    "남은 D-day",
    "입금확인",
    "매칭 횟수",
    "매칭 여부",
    "환불 여부",
]


def _row_jeon() -> list:
    row = [""] * len(NEW_FORM_HEADERS)
    row[0] = "2026. 6. 28 오전 10:05:31"
    row[1] = "전문준"
    row[2] = "남자"
    row[3] = "01076335021"
    row[4] = "AI / AX 엔지니어"
    row[5] = "서울특별시"
    row[16] = "네"
    row[17] = "네"
    row[28] = "#REF!"
    row[29] = "TRUE"
    row[30] = ""
    row[31] = "FALSE"
    row[32] = "FALSE"
    return row


def _row_kim() -> list:
    row = [""] * len(NEW_FORM_HEADERS)
    row[0] = "2026. 7. 1 오후 7:42:47"
    row[1] = "김현진"
    row[2] = "남자"
    row[3] = "01046420312"
    row[4] = "초기 창업가 / CEO"
    row[5] = "인천광역시"
    row[16] = "네"
    row[17] = "네"
    row[28] = "D-14"
    row[29] = "TRUE"
    row[30] = ""
    row[31] = "FALSE"
    row[32] = "FALSE"
    return row


def test_new_form_admin_column_positions():
    assert COL["dday"] == 29
    assert COL["paid"] == 30
    assert COL["reject_count"] == 31
    assert COL["matched"] == 32
    assert COL["refund"] == 33


def test_new_form_header_map_admin_not_consent():
    m = build_column_map(NEW_FORM_HEADERS)
    assert m["paid"] == 29  # 0-based: AD 입금확인
    assert m["refund"] == 32  # AG 환불 여부
    assert m["dday"] == 28
    assert m["name"] == 1
    assert m["job"] == 4


def test_new_form_two_paid_applicants_eligible():
    all_values = [NEW_FORM_HEADERS, _row_jeon(), _row_kim()]
    df = normalize_dataframe(pd.DataFrame(records_from_sheet_values(all_values)))
    assert len(df) == 2
    names = set(df["name"].astype(str))
    assert names == {"전문준", "김현진"}
    assert bool(df.loc[df["name"] == "전문준", "paid"].iloc[0])
    assert bool(df.loc[df["name"] == "김현진", "paid"].iloc[0])
    assert not bool(df.loc[df["name"] == "전문준", "refund"].iloc[0])
    assert df.loc[df["name"] == "김현진", "dday"].iloc[0] == "D-14"
