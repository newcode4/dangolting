"""SNS / Kakao Open Graph — 크롤러가 JS 없이 읽을 정적 meta."""
from __future__ import annotations

import html as html_lib
import os

import streamlit as st

OG_TITLE = "단골팅 — 비즈니스 파트너 매칭"
OG_DESC = (
    "내 사업을 같이 키울 파트너 한 명이면 됩니다. "
    "운영진이 직접 찾아드립니다. 단돈 5만 원 · 소개 없으면 전액 환불."
)
OG_IMAGE_VER = "20260628"


def _public_base_url() -> str:
    try:
        app_cfg = st.secrets.get("app", {})
        url = str(app_cfg.get("public_url", "") or "").strip().rstrip("/")
        if url:
            return url
    except Exception:
        pass
    for key in ("STREAMLIT_SERVER_BASE_URL", "HOSTNAME"):
        val = os.environ.get(key, "").strip().rstrip("/")
        if val.startswith("http"):
            return val
    return ""


def og_image_url(*, base: str = "") -> str:
    root = (base or _public_base_url()).rstrip("/")
    path = f"/app/static/og.svg?v={OG_IMAGE_VER}"
    return f"{root}{path}" if root else path


def inject_og_meta() -> None:
    """HTML meta 태그 — Kakao/Facebook 크롤러용 (JS 실행 불필요)."""
    base = _public_base_url()
    img = og_image_url(base=base)
    tags = [
        ('property="og:type"', "website"),
        ('property="og:site_name"', "단골팅"),
        ('property="og:title"', OG_TITLE),
        ('property="og:description"', OG_DESC),
        ('property="og:image"', img),
        ('property="og:image:width"', "1200"),
        ('property="og:image:height"', "630"),
        ('name="description"', OG_DESC),
        ('name="twitter:card"', "summary_large_image"),
        ('name="twitter:title"', OG_TITLE),
        ('name="twitter:description"', OG_DESC),
        ('name="twitter:image"', img),
    ]
    if base:
        tags.append(('property="og:url"', base + "/"))

    lines = "".join(
        f'<meta {attr} content="{html_lib.escape(val)}"/>' for attr, val in tags
    )
    st.markdown(lines, unsafe_allow_html=True)

    if base:
        return

    # public_url 미설정(로컬) — 브라우저에서 절대 URL 보완
    st.markdown(
        f"""<script>
(function() {{
  var base = window.location.origin + (window.location.pathname || "/");
  base = base.replace(/\\/$/, "");
  var img = base + "/app/static/og.svg?v={OG_IMAGE_VER}";
  [["property","og:image",img],["property","og:url",window.location.href],
   ["name","twitter:image",img]].forEach(function(m) {{
    var el = document.head.querySelector("meta[" + m[0] + '="' + m[1] + '"]');
    if (el) el.setAttribute("content", m[2]);
  }});
}})();
</script>""",
        unsafe_allow_html=True,
    )
