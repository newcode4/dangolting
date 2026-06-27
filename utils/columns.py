"""
실제 구글 폼 시트 헤더 매핑 (단골팅 신청 시트)
"""
from __future__ import annotations

from datetime import datetime

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
    "paid":     "입금확인",
    "matched":  "매칭 여부",
    "reject":   "매칭횟수",      # 거절 누적 — 시트 헤더 '매칭 횟수'
    "matched_w": "_매칭상대",     # 가상 컬럼 (세션/매칭 시 기록)
    "matched_at": "매칭일",
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
    "note":         16,
    "refund_acct":  20,   # T: 환불 받을 계좌 (읽기 전용)
    "dday":         21,   # U: 남은 D-day
    "paid":         22,   # V: 입금확인
    "reject_count": 23,   # W: 매칭 횟수(거절 카운트)
    "matched":      24,   # X: 매칭 여부
    "refund":       25,   # Y: 환불 여부
    "matched_at":   26,   # Z: 매칭일
}

# gspread 1-based 열 → normalize 논리 키 (헤더 문구와 무관하게 고정 위치)
COL_TO_LOGIC: dict[int, str] = {
    COL["timestamp"]: "ts",
    COL["name"]: "name",
    COL["gender"]: "gender",
    COL["contact"]: "contact",
    COL["job"]: "job",
    COL["region"]: "region",
    COL["years"]: "years",
    COL["have"]: "have",
    COL["want_region"]: "w_region",
    COL["want_gender"]: "w_gender",
    COL["want_job"]: "w_job",
    COL["want_years"]: "w_years",
    COL["values"]: "values",
    COL["depth"]: "depth",
    COL["want"]: "want",
    16: "note",
    COL["dday"]: "dday",
    COL["paid"]: "paid",
    COL["reject_count"]: "reject",
    COL["matched"]: "matched",
    COL["refund"]: "refund",
    COL["matched_at"]: "matched_at",
}

# 구글 폼 헤더가 CN 기본값과 다를 때 (열 위치 보조)
HEADER_ALIASES: dict[str, str] = {
    "타임스탬프": "ts",
    "Timestamp": "ts",
    "timestamp": "ts",
    "이름": "name",
    "메인직군": "job",
    "메인 직군": "job",
    "거주/활동지역": "region",
    "거주 / 활동 지역": "region",
    "활동 지역": "region",
    "입금확인": "paid",
    "매칭 횟수": "reject",
    "매칭횟수": "reject",
}

# 헤더 부분 문자열 매칭 (구체적인 패턴을 먼저)
HEADER_PATTERNS: list[tuple[str, tuple[str, ...]]] = [
    ("w_job", ("찾으시는", "상대방의 직군", "희망직")),
    ("w_region", ("매칭 희망", "희망하는 지역", "희망활동")),
    ("w_gender", ("타겟 성별", "희망성별")),
    ("w_years", ("타겟 연차", "희망연차")),
    ("want", ("가장 해결받고", "want")),
    ("depth", ("깊이", "해결의")),
    ("values", ("가치 기준", "가치관")),
    ("have", ("제공가치", "have")),
    ("note", ("하고 싶은 말",)),
    ("paid", ("입금",)),
    ("matched", ("매칭 여부", "매칭여부")),
    ("refund", ("환불",)),
    ("matched_at", ("매칭일",)),
    ("reject", ("매칭 횟수", "매칭횟수", "거절")),
    ("dday", ("d-day", "d day", "남은 d")),
    ("ts", ("타임스탬프", "timestamp", "시간")),
    ("name", ("성함", "이름")),
    ("contact", ("연락", "전화")),
    ("gender", ("성별",)),
    ("years", ("연차",)),
    ("job", ("메인", "직군")),
    ("region", ("거주", "활동지", "지역")),
]

# 논리 키 → 시트 열 (앱에서 편집 가능한 필드)
EDIT_COL: dict[str, int] = {
    "name":     COL["name"],
    "gender":   COL["gender"],
    "contact":  COL["contact"],
    "job":      COL["job"],
    "region":   COL["region"],
    "years":    COL["years"],
    "have":     COL["have"],
    "w_region": COL["want_region"],
    "w_gender": COL["want_gender"],
    "w_job":    COL["want_job"],
    "w_years":  COL["want_years"],
    "values":   COL["values"],
    "depth":    COL["depth"],
    "want":     15,
    "dday":     COL["dday"],
    "reject":   COL["reject_count"],
    "matched":  COL["matched"],
}

EDIT_LABELS: dict[str, str] = {
    "name": "성함",
    "gender": "성별",
    "contact": "연락처",
    "job": "직군",
    "region": "지역",
    "years": "연차",
    "have": "제공가치",
    "w_region": "희망 지역",
    "w_gender": "희망 성별",
    "w_job": "희망 직군",
    "w_years": "희망 연차",
    "values": "가치관",
    "depth": "협업 깊이",
    "want": "원하는 것",
    "dday": "D-day",
    "reject": "매칭횟수(거절)",
    "matched": "매칭 여부",
}

DEFAULT_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1UG_PK_hKOKKbL9sxWCb_M2i3_qHDxE7Q7WqdDk6zJOg/edit"
)
DEFAULT_WORKSHEET = "시트1"

# normalize 후 반드시 존재해야 하는 논리 컬럼 (시트에 없어도 기본값)
COLUMN_DEFAULTS: dict[str, object] = {
    "ts": "",
    "name": "",
    "gender": "",
    "contact": "",
    "job": "",
    "region": "",
    "years": "",
    "have": "",
    "w_region": "",
    "w_gender": "",
    "w_job": "",
    "w_years": "",
    "values": "",
    "depth": "",
    "want": "",
    "note": "",
    "dday": "",
    "paid": False,
    "matched": "",
    "reject": 0,
    "matched_w": "",
    "matched_at": "",
    "refund": False,
}

LOGIC_KEYS: tuple[str, ...] = tuple(k for k in COLUMN_DEFAULTS if k != "matched_w")


def build_column_map(headers: list[str]) -> dict[str, int]:
    """헤더 1행 → 논리 키별 0-based 열 인덱스 (고정 열 번호는 마지막 보조)."""
    stripped = [str(h).strip() for h in headers]
    col_map: dict[str, int] = {}

    def claim(key: str, idx: int) -> None:
        if key not in col_map and 0 <= idx < len(stripped):
            col_map[key] = idx

    cn_items = sorted(
        ((k, v) for k, v in CN.items() if k != "matched_w"),
        key=lambda x: len(x[1]),
        reverse=True,
    )
    for key, header in cn_items:
        for i, h in enumerate(stripped):
            if h == header:
                claim(key, i)
                break

    for i, h in enumerate(stripped):
        if h in HEADER_ALIASES:
            claim(HEADER_ALIASES[h], i)

    for key, needles in HEADER_PATTERNS:
        if key in col_map:
            continue
        for i, h in enumerate(stripped):
            if not h:
                continue
            hl = h.lower()
            if any(n.lower() in hl for n in needles):
                claim(key, i)
                break

    for col_num, key in COL_TO_LOGIC.items():
        claim(key, col_num - 1)

    return col_map


def ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    """논리 키 누락 시 기본값으로 채움 — KeyError 재발 방지."""
    df = df.copy()
    for key, default in COLUMN_DEFAULTS.items():
        if key not in df.columns:
            df[key] = default
    return df


def normalize_dataframe(df: pd.DataFrame, *, apply_eligibility: bool = True) -> pd.DataFrame:
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

    alias_rename: dict[str, str] = {}
    for col in df.columns:
        if col in HEADER_ALIASES:
            target = HEADER_ALIASES[col]
            if target not in df.columns:
                alias_rename[col] = target
    if alias_rename:
        df = df.rename(columns=alias_rename)

    df = ensure_columns(df)

    if "reject" in df.columns:
        df["reject"] = df["reject"].apply(parse_reject)

    if "paid" in df.columns:
        df["paid"] = df["paid"].apply(parse_checkbox)
    if "refund" in df.columns:
        df["refund"] = df["refund"].apply(parse_checkbox)

    if apply_eligibility:
        return apply_eligibility_filter(df)
    return df


def parse_checkbox(val) -> bool:
    """시트 체크박스 → bool (입금확인, 환불 여부 등)."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return False
    if isinstance(val, bool):
        return val
    s = str(val).strip().upper()
    if s in ("", "FALSE", "0", "NO", "N"):
        return False
    if s in ("TRUE", "1", "YES", "Y", "예", "네", "✓", "✔"):
        return True
    try:
        return bool(int(float(val)))
    except (ValueError, TypeError):
        return False


def parse_reject(val) -> int:
    s = str(val).strip().upper()
    if s in ("TRUE", "FALSE", "", "NAN", "NONE"):
        return 0
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0


def apply_eligibility_filter(df: pd.DataFrame) -> pd.DataFrame:
    """입금 확인된 사람만, 환불 처리된 사람은 제외."""
    if df.empty:
        return df
    mask = pd.Series(True, index=df.index)
    if "paid" in df.columns:
        mask &= df["paid"]
    if "refund" in df.columns:
        mask &= ~df["refund"]
    return df[mask].copy()


def now_matched_at() -> str:
    """매칭 확정 시각 문자열."""
    return datetime.now().strftime("%Y. %m. %d %H:%M")


def format_matched_at(val) -> str:
    s = str(val or "").strip()
    if not s or s.lower() in ("nan", "none", ""):
        return ""
    return s


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
