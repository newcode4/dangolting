"""CRM CSS — 파일 기반 · 매 렌더 parent head 주입."""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent.parent
CRM_CSS_PATH = ROOT / "assets" / "crm.css"


def crm_css_inline() -> str:
    css = CRM_CSS_PATH.read_text(encoding="utf-8")
    rev = CRM_CSS_PATH.stat().st_mtime
    return f"/* crm rev:{rev:.0f} */\n{css}"


def inject_crm_styles() -> None:
    """Streamlit rerun마다 DOM이 갈아엎어져 CSS도 매번 재주입."""
    css = crm_css_inline()
    st.markdown(f'<style id="dgt-crm-styles">{css}</style>', unsafe_allow_html=True)
    payload = json.dumps(css)
    components.html(
        f"""<script>
(function () {{
  try {{
    var doc = window.parent.document;
    var id = "dgt-crm-styles";
    var el = doc.getElementById(id);
    if (!el) {{
      el = doc.createElement("style");
      el.id = id;
      doc.head.appendChild(el);
    }}
    el.textContent = {payload};
  }} catch (e) {{}}
}})();
</script>""",
        height=0,
        width=0,
    )
