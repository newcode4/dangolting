"""CRM 운영 설정 — secrets + 기본값."""
from __future__ import annotations

import streamlit as st

from utils.crm_truth import DEFAULT_SLA_UNPAID_HOURS


def _crm_cfg() -> dict:
    try:
        return dict(st.secrets.get("crm", {}))
    except Exception:
        return {}


def sla_unpaid_hours() -> int:
    raw = _crm_cfg().get("sla_unpaid_hours", DEFAULT_SLA_UNPAID_HOURS)
    try:
        n = int(raw)
        return max(1, min(n, 720))
    except (TypeError, ValueError):
        return DEFAULT_SLA_UNPAID_HOURS


def daily_digest_hour() -> int:
    raw = _crm_cfg().get("daily_digest_hour", 12)
    try:
        n = int(raw)
        return max(0, min(n, 23))
    except (TypeError, ValueError):
        return 12
