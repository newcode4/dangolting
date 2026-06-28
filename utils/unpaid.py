"""입금 대기 신청 목록."""
from __future__ import annotations

import pandas as pd

from utils.crm_truth import filter_unpaid_rows


def unpaid_applicants(df: pd.DataFrame) -> pd.DataFrame:
    """입금 대기 — crm_truth.applicant_stage == unpaid."""
    return filter_unpaid_rows(df)
