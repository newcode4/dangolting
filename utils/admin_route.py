"""관리자 전용 URL — 공개 랜딩과 분리."""
from __future__ import annotations

import streamlit as st

ADMIN_QUERY_KEY = "p"
LANDING_PREVIEW_QUERY = "view"
LANDING_PREVIEW_VALUE = "landing"
DEFAULT_ADMIN_PATH = "dgt-manage"


def _auth_cfg() -> dict:
    try:
        return dict(st.secrets.get("auth", {}))
    except Exception:
        return {}


def admin_path_slug() -> str:
    slug = str(_auth_cfg().get("admin_path", DEFAULT_ADMIN_PATH)).strip()
    return slug or DEFAULT_ADMIN_PATH


def admin_entry_path(*, slug: str | None = None) -> str:
    return f"/?{ADMIN_QUERY_KEY}={slug or admin_path_slug()}"


def landing_preview_path() -> str:
    return f"/?{LANDING_PREVIEW_QUERY}={LANDING_PREVIEW_VALUE}"


def is_admin_route() -> bool:
    return st.query_params.get(ADMIN_QUERY_KEY, "").strip() == admin_path_slug()


def is_landing_preview_route() -> bool:
    return st.query_params.get(LANDING_PREVIEW_QUERY, "") == LANDING_PREVIEW_VALUE
