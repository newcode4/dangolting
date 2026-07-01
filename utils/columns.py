"""
실제 구글 폼 시트 헤더 매핑 (단골팅 신청 시트)
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd
# 논리 키 → 실제 시트 헤더 (strip 후 비교)
CN: dict[str, str] = {
    "ts":       "타임스탬프",
    "name":     "성함",
    "gender":   "본인의 성별을 알려주세요.",
    "contact":  "연락처",
    "job":      "나의 직군은 무엇인가요?",
    "region":   "주로 활동하시는 지역(위치)은 어디인가요?",
    "years":    "나의 현재 전문성 및 연차 체급은 어느 정도인가요?",
    "have":     "상대방에게 당장 제공할 수 있는 나의 '비즈니스 자산'은 무엇인가요?",
    "w_region": "매칭 희망하는 지역",
    "w_gender": "매칭 성별 선호도",
    "w_job":    "찾으시는 상대방의 직군은 무엇인가요?",
    "w_years":  "상대방에게 기대하는 연차 무엇인가요?",
    "values":   "비즈니스를 하거나 내 일을 할 때, 내가 가장 중요하게 생각하는 가치는 무엇인가요?",
    "depth":    "내가 상대방에게 바라는 문제 해결의 깊이는 어느 정도인가요?",
    "want":     "지금 내 사업에서 '가장 답답하고 막막한 부분'은 어디인가요?",
    "note":     "추가적으로 하고 싶은 말",
    "paid_self": "단골팅 참가비 입금을 완료하셨나요",
    "agree_refund": "단골팅 환불 및 진행 규칙에 동의하십니까?",
    "agree_privacy": "개인정보 수집 및 이용 동의 하십니까?",
    "refund_acct": "환불 받을 계좌를 알려주세요",
    "have_action": "제공할 가치의 '정확한 알맹이(행동)'를 알려주세요.",
    "have_where": "상대방이 '어떤 자료'를 들고 오거나, '어디로' 오면 그걸 해줄 수 있나요?",
    "product": "지금 돈을 벌고 있거나, 준비 중인 '아이템/서비스'는 무엇인가요?",
    "pain_today": "그 아이템을 굴리면서 '오늘 당장 내 머리를 싸매게 만드는 가장 골치 아픈   문제'는 무엇인가요?",
    "worth_it": "상대방이 나에게 '이렇게까지 해주면 이번 단골팅 5만원이 전혀 아깝지 않겠다' 하는 구체적인 모습을 적어주세요.",
    "portfolio": "나의 전문성을 보여줄 수 있는 포트폴리오나 참고 링크가 있다면 남겨주세요. (없다면 '없음' 입력)",
    "buyer_intent": "단골팅은 서로 대등하게 돕는 '파트너십' 매칭입니다. 혹시 \"내 제품을 살 고객(바이어)을 찾고 싶다\"는 목적이신가요?",
    "dday":     "남은 D-day",
    "paid":     "입금확인",
    "matched":  "매칭 여부",
    "reject":   "매칭 횟수",
    "matched_w": "_매칭상대",
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
    "paid_self":    17,
    "agree_refund": 18,
    "agree_privacy": 19,
    "refund_acct":  20,
    "have_action":  21,
    "have_where":   22,
    "product":      23,
    "pain_today":   24,
    "worth_it":     25,
    "portfolio":    26,
    "buyer_intent": 27,
    "dday":         29,   # AC: 남은 D-day
    "paid":         30,   # AD: 입금확인 (관리자)
    "reject_count": 31,   # AE: 매칭 횟수
    "matched":      32,   # AF: 매칭 여부
    "refund":       33,   # AG: 환불 여부
    "matched_at":   34,   # AH: 매칭일 (있을 때)
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
    COL["paid_self"]: "paid_self",
    COL["agree_refund"]: "agree_refund",
    COL["agree_privacy"]: "agree_privacy",
    COL["refund_acct"]: "refund_acct",
    COL["have_action"]: "have_action",
    COL["have_where"]: "have_where",
    COL["product"]: "product",
    COL["pain_today"]: "pain_today",
    COL["worth_it"]: "worth_it",
    COL["portfolio"]: "portfolio",
    COL["buyer_intent"]: "buyer_intent",
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

# 헤더 부분 문자열 매칭 (구체적인 패턴을 먼저 — 동의 문항 vs 관리 열 구분)
HEADER_PATTERNS: list[tuple[str, tuple[str, ...]]] = [
    ("paid", ("입금확인",)),
    ("refund", ("환불 여부",)),
    ("matched", ("매칭 여부", "매칭여부")),
    ("reject", ("매칭 횟수", "매칭횟수")),
    ("dday", ("남은 d-day", "남은 d day", "남은 d")),
    ("matched_at", ("매칭일",)),
    ("w_job", ("찾으시는", "상대방의 직군", "희망직")),
    ("w_region", ("매칭 희망하는 지역", "희망하는 지역", "희망활동")),
    ("w_gender", ("매칭 성별", "타겟 성별", "희망성별")),
    ("w_years", ("기대하는 연차", "타겟 연차", "희망연차")),
    ("want", ("답답하고 막막한", "가장 해결받고", "want")),
    ("depth", ("문제 해결의 깊이", "깊이")),
    ("values", ("중요하게 생각하는 가치", "가치 기준", "가치관")),
    ("have", ("비즈니스 자산", "제공가치", "have")),
    ("note", ("추가적으로 하고 싶은 말", "하고 싶은 말")),
    ("paid_self", ("참가비 입금을 완료",)),
    ("agree_refund", ("환불 및 진행 규칙",)),
    ("agree_privacy", ("개인정보 수집", "개인정보")),
    ("refund_acct", ("환불 받을 계좌",)),
    ("have_action", ("정확한 알맹이", "행동")),
    ("have_where", ("어떤 자료", "어디로")),
    ("product", ("아이템/서비스", "돈을 벌고")),
    ("pain_today", ("골치 아픈", "머리를 싸매")),
    ("worth_it", ("5만원이 전혀 아깝지", "아깝지 않겠다")),
    ("portfolio", ("포트폴리오", "참고 링크")),
    ("buyer_intent", ("바이어", "고객(바이어)")),
    ("ts", ("타임스탬프", "timestamp", "시간")),
    ("name", ("성함", "이름")),
    ("contact", ("연락", "전화")),
    ("gender", ("본인의 성별", "성별")),
    ("years", ("연차 체급", "연차")),
    ("job", ("나의 직군", "메인", "직군")),
    ("region", ("활동하시는 지역", "거주", "활동지", "지역")),
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
    "paid_self": "",
    "agree_refund": "",
    "agree_privacy": "",
    "refund_acct": "",
    "have_action": "",
    "have_where": "",
    "product": "",
    "pain_today": "",
    "worth_it": "",
    "portfolio": "",
    "buyer_intent": "",
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
