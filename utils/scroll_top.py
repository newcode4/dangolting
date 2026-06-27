"""관리자 화면 진입 시 부모 스크롤을 맨 위로."""
from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

_SCROLL_RESET_KEY = "_admin_scroll_reset"


def reset_page_scroll(*, force: bool = False) -> None:
    """랜딩 스크롤 잔여 위치 제거 — 로그인·대시보드 진입 시 1회."""
    if not force and st.session_state.get(_SCROLL_RESET_KEY):
        return
    st.session_state[_SCROLL_RESET_KEY] = True
    components.html(
        """<script>
        (function () {
          try {
            var p = window.parent;
            p.scrollTo(0, 0);
            var el = p.document.scrollingElement || p.document.documentElement;
            if (el) el.scrollTop = 0;
          } catch (e) {}
          window.scrollTo(0, 0);
        })();
        </script>""",
        height=0,
    )
