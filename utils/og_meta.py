"""SNS / Kakao Open Graph — parent head + 절대 URL PNG."""
from __future__ import annotations

import html as html_lib
import json
import os

import streamlit as st
import streamlit.components.v1 as components

OG_TITLE = "단골팅 — 비즈니스 파트너 매칭"
OG_DESC = (
    "내 사업을 같이 키울 파트너 한 명이면 됩니다. "
    "운영진이 직접 찾아드립니다. 단돈 5만 원 · 소개 없으면 전액 환불."
)
OG_IMAGE_VER = "20260629"
DEFAULT_PUBLIC_URL = "https://dangolting-fusxuqj52c7scbvcuduiej.streamlit.app"
GITHUB_RAW_OG = (
    f"https://raw.githubusercontent.com/newcode4/dangolting/main/static/og.png?v={OG_IMAGE_VER}"
)


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
    return DEFAULT_PUBLIC_URL


def og_image_url(*, base: str = "") -> str:
    """Kakao용 — GitHub raw PNG (크롤러·CDN 안정). Streamlit static는 보조."""
    root = (base or _public_base_url()).rstrip("/")
    app_png = f"{root}/app/static/og.png?v={OG_IMAGE_VER}"
    # raw.githubusercontent.com 이 배포 직후에도 즉시 fetch 가능
    return GITHUB_RAW_OG if OG_IMAGE_VER else app_png


def _meta_pairs(base: str) -> list[tuple[str, str, str]]:
    img = og_image_url(base=base)
    pairs: list[tuple[str, str, str]] = [
        ("property", "og:type", "website"),
        ("property", "og:site_name", "단골팅"),
        ("property", "og:title", OG_TITLE),
        ("property", "og:description", OG_DESC),
        ("property", "og:image", img),
        ("property", "og:image:secure_url", img),
        ("property", "og:image:type", "image/png"),
        ("property", "og:image:width", "1200"),
        ("property", "og:image:height", "630"),
        ("property", "og:url", base + "/"),
        ("name", "description", OG_DESC),
        ("name", "twitter:card", "summary_large_image"),
        ("name", "twitter:title", OG_TITLE),
        ("name", "twitter:description", OG_DESC),
        ("name", "twitter:image", img),
    ]
    return pairs


def inject_og_meta() -> None:
    """parent document <head> + body — Kakao·Facebook 스크래퍼 대응."""
    base = _public_base_url()
    pairs = _meta_pairs(base)

    body_tags = "".join(
        f'<meta {k}="{html_lib.escape(n)}" content="{html_lib.escape(v)}"/>'
        for k, n, v in pairs
    )
    st.markdown(body_tags, unsafe_allow_html=True)

    payload = json.dumps([[k, n, v] for k, n, v in pairs], ensure_ascii=False)
    title_json = json.dumps(OG_TITLE, ensure_ascii=False)
    components.html(
        f"""<script>
(function () {{
  var metas = {payload};
  var title = {title_json};
  function apply(doc) {{
    if (!doc || !doc.head) return;
    metas.forEach(function (m) {{
      var el = doc.head.querySelector('meta[' + m[0] + '="' + m[1] + '"]');
      if (!el) {{
        el = doc.createElement("meta");
        el.setAttribute(m[0], m[1]);
        doc.head.appendChild(el);
      }}
      el.setAttribute("content", m[2]);
    }});
    if (doc.title !== title) doc.title = title;
  }}
  try {{
    apply(document);
    apply(window.parent.document);
  }} catch (e) {{}}
}})();
</script>""",
        height=0,
        width=0,
    )
