"""Streamlit Cloud 크롬(배지·GitHub·앱 제작자 아바타) 숨김 — parent head 직접 주입."""
from __future__ import annotations

import json

import streamlit as st
import streamlit.components.v1 as components

# body.dgt-landing 불필요 — Streamlit Cloud UI는 parent document에 렌더
SHELL_HIDE_CSS = """
#GithubIcon,
[class*="GithubIcon"],
[class*="profileContainer"],
[class*="profilePreview"],
[class*="profileImage"],
[data-testid="appCreatorAvatar"],
img[alt="App Creator Avatar"],
a[href*="share.streamlit.io/user"],
a[href*="avatars.githubusercontent.com"],
[class*="viewerBadge"],
[data-testid="stBottom"],
[data-testid="stBottomBlockContainer"],
[data-testid="stStatusWidget"],
[data-testid="stAppDeployButton"],
[data-testid="manageAppButton"],
.stAppDeployButton,
a[href*="github.com"][target="_blank"],
a[href*="streamlit.io/cloud"][target="_blank"] {
  display: none !important;
  visibility: hidden !important;
  opacity: 0 !important;
  pointer-events: none !important;
  max-height: 0 !important;
  max-width: 0 !important;
  overflow: hidden !important;
  position: fixed !important;
  left: -9999px !important;
  top: -9999px !important;
  z-index: -1 !important;
  width: 0 !important;
  height: 0 !important;
}
"""

_HIDE_SELECTORS = [
    "#GithubIcon",
    '[class*="GithubIcon"]',
    '[class*="profileContainer"]',
    '[class*="profilePreview"]',
    '[class*="profileImage"]',
    '[data-testid="appCreatorAvatar"]',
    'img[alt="App Creator Avatar"]',
    'a[href*="share.streamlit.io/user"]',
    'a[href*="avatars.githubusercontent.com"]',
    '[class*="viewerBadge"]',
    '[data-testid="stBottom"]',
    '[data-testid="stBottomBlockContainer"]',
    '[data-testid="stStatusWidget"]',
    '[data-testid="stAppDeployButton"]',
    '[data-testid="manageAppButton"]',
    ".stAppDeployButton",
    'a[href*="github.com"]',
]

_HIDE_JS = """
function dgtHideNode(node) {
  if (!node || !node.style) return;
  node.style.setProperty("display", "none", "important");
  node.style.setProperty("visibility", "hidden", "important");
  node.style.setProperty("opacity", "0", "important");
  node.style.setProperty("pointer-events", "none", "important");
  node.style.setProperty("width", "0", "important");
  node.style.setProperty("height", "0", "important");
}
function dgtHideCreatorProfile(doc) {
  if (!doc) return;
  doc.querySelectorAll('[data-testid="appCreatorAvatar"]').forEach(function (img) {
    dgtHideNode(img);
    var link = img.closest('a[href*="share.streamlit.io"]');
    if (link) dgtHideNode(link);
    var box = img.closest('[class*="profileContainer"]');
    if (box) dgtHideNode(box);
    var preview = img.closest('[class*="profilePreview"]');
    if (preview) dgtHideNode(preview);
  });
}
function dgtHideChrome(doc) {
  if (!doc || !doc.head) return;
  var css = __CSS__;
  var id = "dgt-shell-hide";
  var el = doc.getElementById(id);
  if (!el) {
    el = doc.createElement("style");
    el.id = id;
    doc.head.appendChild(el);
  }
  el.textContent = css;
  __SELECTORS__.forEach(function (sel) {
    doc.querySelectorAll(sel).forEach(dgtHideNode);
  });
  dgtHideCreatorProfile(doc);
}
"""


def inject_streamlit_cloud_chrome_hide() -> None:
    """매 rerun parent + iframe document에 숨김 CSS·Observer."""
    st.markdown(f'<style id="dgt-shell-hide">{SHELL_HIDE_CSS}</style>', unsafe_allow_html=True)
    css_json = json.dumps(SHELL_HIDE_CSS)
    selectors_json = json.dumps(_HIDE_SELECTORS)
    hide_js = (
        _HIDE_JS.replace("__CSS__", css_json).replace("__SELECTORS__", selectors_json)
    )
    components.html(
        f"""<script>
(function () {{
  {hide_js}
  function boot(doc) {{
    dgtHideChrome(doc);
    if (!doc.__dgtShellObserver) {{
      doc.__dgtShellObserver = new MutationObserver(function () {{ dgtHideChrome(doc); }});
      doc.__dgtShellObserver.observe(doc.documentElement, {{ childList: true, subtree: true }});
    }}
  }}
  try {{ boot(document); }} catch (e) {{}}
  try {{ boot(window.parent.document); }} catch (e) {{}}
}})();
</script>""",
        height=0,
        width=0,
    )
