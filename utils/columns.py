"""
실제 구글 폼 시트 헤더 매핑 (단골팅 신청 시트)
"""
from __future__ import annotations

import pandas as pd

# 논리 키 → 실제 시트 헤더 (strip 후 비교)
CN: dict[str, str] = {
    "ts":       "시간",
    "name":     "성함",
    "gender":   "성별",
    "contact":  "연락처",
    "job":      "직군",
    "region":   "지역",
    "years":    "연차",
    "have":     "제공가치",
    "w_region": "매칭 희망하는 지역",
    "w_gender": "타겟 성별",
    "w_job":    "찾으시는 상대방의 직군은 무엇인가요?",
    "w_years":  "타겟 연차",
    "values":   "중요 가치 기준",
    "depth":    "내가 상대방에게 바라는 문제 해결의 깊이는 어느 정도인가요?",
    "want":     "이번 매칭을 통해 상대방에게 '가장 해결받고 싶은 현재 나의 문제'는 무엇인가요?",
    "note":     "추가적으로 하고 싶은 말",
    "dday":     "남은 D-day",
    "matched":  "매칭 여부",
    "reject":   "매칭횟수",      # 거절 누적 카운트로 사용
    "matched_w": "_매칭상대",     # 가상 컬럼 (세션/매칭 시 기록)
    "refund":   "환불 여부",
}

# gspread 1-based 열 번호
COL: dict[str, int] = {
    "timestamp":    1,
    "name":         2,
    "gender":       3,
    "contact":      4,
    "job":          5,
    "region":       6,
    "years":        7,
    "have":         8,
    "want_region":  9,
    "want_gender":  10,
    "want_job":     11,
    "want_years":   12,
    "values":       13,
    "depth":        14,
    "want":         15,
    "dday":         20,
    "reject_count": 21,   # 매칭횟수
    "matched":      22,   # 매칭 여부
    "refund":       23,   # 환불 여부
}

DEFAULT_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1UG_PK_hKOKKbL9sxWCb_M2i3_qHDxE7Q7WqdDk6zJOg/edit"
)
DEFAULT_WORKSHEET = "시트1"


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """헤더 공백 제거 + 논리 키 컬럼으로 정규화."""
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    rename: dict[str, str] = {}
    for key, header in CN.items():
        if key == "matched_w":
            continue
        if header in df.columns:
            rename[header] = key

    df = df.rename(columns=rename)

    if "matched_w" not in df.columns:
        df["matched_w"] = ""

    if "reject" not in df.columns:
        df["reject"] = 0
    else:
        df["reject"] = df["reject"].apply(parse_reject)

    return df


def parse_reject(val) -> int:
    s = str(val).strip().upper()
    if s in ("TRUE", "FALSE", "", "NAN", "NONE"):
        return 0
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0


def col(df: pd.DataFrame, key: str):
    """논리 키로 Series 반환."""
    if key in df.columns:
        return df[key]
    header = CN.get(key, key)
    if header in df.columns:
        return df[header]
    raise KeyError(f"컬럼 없음: {key} ({header})")


def cell(row: pd.Series, key: str, default=""):
    """행에서 논리 키 값 조회."""
    if key in row.index:
        v = row[key]
        return default if pd.isna(v) else v
    header = CN.get(key, key)
    if header in row.index:
        v = row[header]
        return default if pd.isna(v) else v
    return default
