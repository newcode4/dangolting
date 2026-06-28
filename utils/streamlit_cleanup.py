"""이전 배포가 parent document에 남긴 Observer·CSS 정리 (무한 로딩 방지)."""
from __future__ import annotations

import streamlit.components.v1 as components


def cleanup_stale_streamlit_shell() -> None:
    """dgt-shell-hide / MutationObserver 잔여물 제거 — revert 후에도 blank·무한로딩 방지."""
    components.html(
        """<script>
(function () {
  function clean(doc) {
    if (!doc) return;
    try {
      if (doc.__dgtShellObserver) {
        doc.__dgtShellObserver.disconnect();
        doc.__dgtShellObserver = null;
      }
    } catch (e) {}
    try {
      if (doc.__dgtBadgeObserver) {
        doc.__dgtBadgeObserver.disconnect();
        doc.__dgtBadgeObserver = null;
      }
    } catch (e) {}
    ["dgt-shell-hide"].forEach(function (id) {
      var el = doc.getElementById(id);
      if (el) el.remove();
    });
  }
  try { clean(document); } catch (e) {}
  try { clean(window.parent.document); } catch (e) {}
})();
</script>""",
        height=0,
        width=0,
    )
