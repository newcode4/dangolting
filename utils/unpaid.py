"""입금 대기 신청 목록."""
from __future__ import annotations

import pandas as pd

from utils.columns import parse_checkbox


def unpaid_applicants(df: pd.DataFrame) -> pd.DataFrame:
    """입금 미확인 · 환불 아님."""
    if df.empty:
        return df
    out = df.copy()
    paid = out["paid"].apply(parse_checkbox) if "paid" in out.columns else pd.Series(False, index=out.index)
    refund = out["refund"].apply(parse_checkbox) if "refund" in out.columns else pd.Series(False, index=out.index)
    mask = ~paid & ~refund
    if "name" in out.columns:
        mask &= out["name"].astype(str).str.strip().astype(bool)
    return out[mask].sort_index()
