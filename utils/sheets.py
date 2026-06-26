"""
Google Sheets 연동 모듈
"""
from __future__ import annotations

import os
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

from utils.columns import COL, EDIT_COL, normalize_dataframe, DEFAULT_WORKSHEET, parse_reject
from utils.error_log import log_exception

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

HEADER_ROW = 1


def _get_client() -> gspread.Client:
    try:
        if "gcp_service_account" in st.secrets:
            info = dict(st.secrets["gcp_service_account"])
            creds = Credentials.from_service_account_info(info, scopes=SCOPES)
            return gspread.authorize(creds)
    except Exception:
        pass

    cred_path = os.path.join(os.path.dirname(__file__), "..", "credentials.json")
    if os.path.exists(cred_path):
        creds = Credentials.from_service_account_file(cred_path, scopes=SCOPES)
        return gspread.authorize(creds)

    raise FileNotFoundError(
        "Google 인증 정보를 찾을 수 없습니다.\n"
        "credentials.json을 프로젝트 루트에 놓거나, "
        ".streamlit/secrets.toml에 [gcp_service_account]를 설정하세요."
    )


@st.cache_resource(ttl=0)
def _get_worksheet(sheet_url: str, worksheet_name: str) -> gspread.Worksheet:
    client = _get_client()
    spreadsheet = client.open_by_url(sheet_url)
    return spreadsheet.worksheet(worksheet_name)


def load_data(sheet_url: str, worksheet_name: str = DEFAULT_WORKSHEET) -> pd.DataFrame:
    return load_data_raw(sheet_url, worksheet_name, apply_eligibility=True)


def load_data_raw(
    sheet_url: str,
    worksheet_name: str = DEFAULT_WORKSHEET,
    *,
    apply_eligibility: bool = True,
) -> pd.DataFrame:
    try:
        ws = _get_worksheet(sheet_url, worksheet_name)
        records = ws.get_all_records(head=HEADER_ROW)
        df = pd.DataFrame(records)
        if df.empty:
            return df

        df.index = df.index + HEADER_ROW + 1
        df["_row"] = df.index
        return normalize_dataframe(df, apply_eligibility=apply_eligibility)
    except Exception as exc:
        log_exception(exc, where="sheets.load_data_raw", extra=f"{worksheet_name}")
        raise


def update_cell(sheet_url: str, row: int, col: int, value, worksheet_name: str = DEFAULT_WORKSHEET) -> None:
    ws = _get_worksheet(sheet_url, worksheet_name)
    ws.update_cell(row, col, value)


def set_matched(
    sheet_url: str,
    row: int,
    matched_with: str,
    matched_at: str,
    worksheet_name: str = DEFAULT_WORKSHEET,
) -> None:
    """매칭 완료: W열=TRUE, Y열=매칭일."""
    ws = _get_worksheet(sheet_url, worksheet_name)
    cells = [
        {"range": gspread.utils.rowcol_to_a1(row, COL["matched"]), "values": [["TRUE"]]},
        {"range": gspread.utils.rowcol_to_a1(row, COL["matched_at"]), "values": [[matched_at]]},
    ]
    ws.batch_update(cells, value_input_option="USER_ENTERED")


def increment_reject(sheet_url: str, row: int, current_count: int, worksheet_name: str = DEFAULT_WORKSHEET) -> int:
    new_count = current_count + 1
    update_cell(sheet_url, row, COL["reject_count"], new_count, worksheet_name)
    return new_count


def update_profile_fields(
    sheet_url: str,
    row: int,
    fields: dict[str, object],
    worksheet_name: str = DEFAULT_WORKSHEET,
) -> None:
    """프로필 필드 여러 개를 시트에 반영."""
    ws = _get_worksheet(sheet_url, worksheet_name)
    cells: list[dict] = []
    for key, value in fields.items():
        if key == "matched_at":
            col = COL["matched_at"]
        else:
            col = EDIT_COL.get(key)
        if col is None:
            continue
        if key == "reject":
            value = parse_reject(value)
        elif key == "matched":
            value = "TRUE" if str(value).strip().upper() in ("TRUE", "1", "YES", "완료") else ""
        cells.append({"range": gspread.utils.rowcol_to_a1(row, col), "values": [[value]]})
    if cells:
        ws.batch_update(cells, value_input_option="USER_ENTERED")


from utils.demo_data import DEMO_DATA


def load_demo_data() -> pd.DataFrame:
    df = pd.DataFrame(DEMO_DATA)
    df.index = df["_row"]
    # 데모는 UI 확인용 — 입금/환불 eligibility 필터 적용하지 않음
    return normalize_dataframe(df, apply_eligibility=False)
