"""
단골팅 관리자 — 매칭 작업실
"""
from __future__ import annotations

import html as html_lib
import re
from datetime import timedelta
from pathlib import Path
from urllib.parse import quote

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

from utils.matching import recommend, score_label, evaluate
from utils.value_match import story_block_html, value_badge_html
from utils.ui_components import recommendation_card_html
from utils.match_display import keywords_html, apply_keyword_filter, MatchKeyword, analyze_pair, _theme
from utils.columns import DEFAULT_SHEET_URL, DEFAULT_WORKSHEET, parse_reject, parse_checkbox, EDIT_LABELS, now_matched_at, format_matched_at
from utils.sheets import load_data, load_data_raw, load_demo_data, set_matched, increment_reject, update_profile_fields
from utils.filters import (
    FILTER_FIELDS,
    field_options,
    option_label,
    collect_filter_selections,
    apply_field_filters,
    active_filter_labels,
    clear_all_filters,
)
from utils.date_filter import render_global_date_filter, apply_date_filter
from utils.search_index import search_df, drop_search_index, ensure_search_index
from utils.data_loader import expected_data_source, should_reload_df
from utils.sheet_prefs import active_sheet_config, load_sheet_prefs, save_sheet_prefs
from utils.auth import ensure_authenticated, current_user, logout
from utils.error_log import setup_logging, install_excepthook, ui_error, tail_log, log_exception
from utils.unpaid import unpaid_applicants
from utils.telegram_notify import (
    telegram_enabled,
    telegram_config_status,
    poll_interval_seconds,
    run_applicant_watch,
    send_test_notification,
    reset_notify_baseline,
)

ROOT = Path(__file__).resolve().parent
LOGO = ROOT / "assets" / "logo-mark.svg"

setup_logging()
install_excepthook()

LOGO_SVG_FALLBACK = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" fill="none">
  <rect width="48" height="48" rx="12" fill="#5B8DEF" fill-opacity="0.16"/>
  <rect width="48" height="48" rx="12" stroke="#5B8DEF" stroke-opacity="0.38" stroke-width="1"/>
  <circle cx="17" cy="24" r="7" fill="#5B8DEF"/>
  <circle cx="31" cy="24" r="7" fill="#3D9970"/>
  <path d="M22.5 24h3" stroke="#E8E8EC" stroke-width="2" stroke-linecap="round" stroke-opacity="0.85"/>
  <path d="M21 19.5c1.2-2.2 4.8-2.2 6 0" stroke="#5DDBA4" stroke-width="1.6" stroke-linecap="round" fill="none"/>
</svg>"""


def _read_logo_svg() -> str:
    if LOGO.is_file():
        try:
            return LOGO.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return LOGO.read_text(encoding="utf-8", errors="replace")
    return LOGO_SVG_FALLBACK


def logo_data_uri() -> str:
    return "data:image/svg+xml," + quote(_read_logo_svg())


def ensure_sidebar_visible() -> None:
    """접힌 사이드바를 자동으로 다시 펼침 (CSS 보조)."""
    components.html(
        """<script>
        (function () {
          const doc = window.parent.document;
          const sb = doc.querySelector('[data-testid="stSidebar"]');
          if (!sb || sb.getAttribute('aria-expanded') !== 'false') return;
          const btn = doc.querySelector('[data-testid="stSidebarCollapsedControl"] button')
            || doc.querySelector('[data-testid="collapsedControl"] button');
          if (btn) btn.click();
        })();
        </script>""",
        height=0,
        width=0,
    )


st.set_page_config(
    page_title="단골팅",
    page_icon=str(LOGO),
    layout="wide",
    initial_sidebar_state="expanded",
)

THEME_CSS = (ROOT / "assets" / "theme.css").read_text(encoding="utf-8")
st.markdown(f"<style>{THEME_CSS}</style>", unsafe_allow_html=True)

ensure_authenticated(logo_data_uri())
ensure_sidebar_visible()

for k, v in [
    ("df", None), ("selected", []), ("demo_mode", True), ("load_ver", 0), ("flash", ""),
    ("chip_filter", None), ("mob_view", "list"), ("focus_settings", False),
    ("_df_source", None),
]:
    if k not in st.session_state:
        st.session_state[k] = v

if "saved_sheet_url" not in st.session_state:
    file_url, file_ws = load_sheet_prefs()
    legacy_url = st.session_state.pop("sheet_url", None)
    legacy_ws = st.session_state.pop("ws_name", None)
    st.session_state["saved_sheet_url"] = (legacy_url or file_url or DEFAULT_SHEET_URL).strip()
    st.session_state["saved_ws_name"] = (legacy_ws or file_ws or DEFAULT_WORKSHEET).strip()
# 이전 버전 호환
if st.session_state.get("selected_idx") is not None and not st.session_state["selected"]:
    st.session_state["selected"] = [st.session_state.pop("selected_idx")]


def _refresh_data() -> None:
    st.session_state["load_ver"] += 1
    st.session_state["df"] = None
    st.session_state.pop("_df_source", None)
    st.session_state["selected"] = []
    st.session_state["mob_view"] = "list"


# eligibility 버그 등으로 빈 df가 session에 남은 경우 자동 복구
if (
    st.session_state.get("demo_mode", True)
    and st.session_state.get("df") is not None
    and st.session_state["df"].empty
):
    _refresh_data()


def _saved_sheet_url() -> str:
    return str(st.session_state.get("saved_sheet_url", DEFAULT_SHEET_URL) or DEFAULT_SHEET_URL)


def _saved_ws_name() -> str:
    return str(st.session_state.get("saved_ws_name", DEFAULT_WORKSHEET) or DEFAULT_WORKSHEET)


def render_telegram_controls(*, key_prefix: str) -> None:
    st.caption(f"📱 텔레그램 — {telegram_config_status()}")
    if telegram_enabled():
        st.caption(f"앱 폴링 · 약 {poll_interval_seconds() // 60}분 (권장: Apps Script만 사용 시 enabled=false)")
        stacked = key_prefix.startswith("side_")

        def _btn_test() -> None:
            if send_test_notification():
                st.toast("테스트 알림을 보냈습니다")
            else:
                st.error("발송 실패 — bot_token · chat_id · 봇 /start 확인")

        def _btn_poll() -> None:
            if st.session_state["demo_mode"] or not _saved_sheet_url():
                st.info("데모 끄고 실제 시트 연동 후 사용하세요")
            else:
                n = run_applicant_watch(_saved_sheet_url(), _saved_ws_name())
                st.toast(f"알림 {n}건 발송" if n else "새 신청 없음 (또는 이미 알림 보냄)")

        def _btn_baseline() -> None:
            if not st.session_state["demo_mode"] and _saved_sheet_url():
                reset_notify_baseline(_saved_sheet_url(), _saved_ws_name())
                st.toast("알림 기준선을 현재 시트로 맞췄습니다")
            else:
                st.info("데모 끄고 실제 시트 연동 후 사용하세요")

        if stacked:
            if st.button("알림 테스트", key=f"{key_prefix}tg_test", use_container_width=True):
                _btn_test()
            if st.button("지금 확인", key=f"{key_prefix}tg_poll", use_container_width=True):
                _btn_poll()
            if st.button("기준선", key=f"{key_prefix}tg_reset", use_container_width=True):
                _btn_baseline()
            st.caption("기준선 — 지금까지 신청은 알림에서 제외")
        else:
            tg1, tg2, tg3 = st.columns(3, gap="small")
            with tg1:
                if st.button("알림 테스트", key=f"{key_prefix}tg_test", use_container_width=True):
                    _btn_test()
            with tg2:
                if st.button("지금 확인", key=f"{key_prefix}tg_poll", use_container_width=True):
                    _btn_poll()
            with tg3:
                if st.button("기준선", key=f"{key_prefix}tg_reset", use_container_width=True):
                    _btn_baseline()
            st.caption("기준선 — 지금까지 신청은 알림에서 제외")
    else:
        st.caption("알림: **시트 Apps Script** — 새 신청 즉시 · U열 입금 · **매일 12시** 입금대기 묶음")
        st.caption("설정 · 알림 탭 → Code.gs · `installTriggers` 실행")


def render_settings_panel(*, key_prefix: str) -> None:
    st.caption(f"접속: {current_user()}")
    if st.button("로그아웃", key=f"{key_prefix}logout", use_container_width=True):
        logout()
        st.rerun()

    prev_demo = st.session_state.get("demo_mode")
    demo_on = st.toggle("데모 데이터", value=st.session_state["demo_mode"], key=f"{key_prefix}demo")
    if prev_demo is not None and prev_demo != demo_on:
        _refresh_data()
    st.session_state["demo_mode"] = demo_on

    if not demo_on:
        st.caption("시트 연동 중 · 변경은 새로고침으로 불러옴")
        new_url = st.text_input(
            "시트 주소",
            value=_saved_sheet_url(),
            key=f"{key_prefix}sheet_url",
            label_visibility="collapsed",
        )
        new_ws = st.text_input(
            "시트 탭",
            value=_saved_ws_name(),
            key=f"{key_prefix}ws_name",
            label_visibility="collapsed",
        )
        if new_url != _saved_sheet_url() or new_ws != _saved_ws_name():
            url = new_url.strip() or DEFAULT_SHEET_URL
            ws = new_ws.strip() or DEFAULT_WORKSHEET
            st.session_state["saved_sheet_url"] = url
            st.session_state["saved_ws_name"] = ws
            save_sheet_prefs(url, ws)
    else:
        st.caption("데모 모드 — 시트 설정은 유지됩니다")
        st.text_input(
            "시트 주소 (보존)",
            value=_saved_sheet_url(),
            disabled=True,
            key=f"{key_prefix}sheet_url_ro",
            label_visibility="collapsed",
        )
        st.text_input(
            "시트 탭 (보존)",
            value=_saved_ws_name(),
            disabled=True,
            key=f"{key_prefix}ws_name_ro",
            label_visibility="collapsed",
        )

    if st.button("새로고침", key=f"{key_prefix}refresh", use_container_width=True):
        _refresh_data()
        st.rerun()

    render_telegram_controls(key_prefix=key_prefix)

    with st.expander("오류 로그 (최근)", expanded=False):
        st.caption(f"파일: data/logs/app.log")
        st.code(tail_log(60), language="log")


with st.sidebar:
    _logo = logo_data_uri()
    st.markdown(
        f'<div class="sidebar-brand">'
        f'<img src="{_logo}" alt="단골팅"/>'
        f'<span>단골팅</span></div>',
        unsafe_allow_html=True,
    )
    st.caption("설정")
    render_settings_panel(key_prefix="side_")

demo_mode = st.session_state["demo_mode"]
sheet_url, ws_name = active_sheet_config(
    demo_mode=demo_mode,
    saved_url=_saved_sheet_url(),
    saved_ws=_saved_ws_name(),
)

if telegram_enabled():
    _poll = poll_interval_seconds()

    if not demo_mode and sheet_url and not st.session_state.get("_tg_boot_watch"):
        st.session_state["_tg_boot_watch"] = True
        try:
            run_applicant_watch(sheet_url, ws_name)
        except Exception as exc:
            log_exception(exc, where="telegram.boot")

    @st.fragment(run_every=timedelta(seconds=_poll))
    def applicant_telegram_watch() -> None:
        try:
            url, ws = active_sheet_config(
                demo_mode=st.session_state.get("demo_mode", True),
                saved_url=_saved_sheet_url(),
                saved_ws=_saved_ws_name(),
            )
            if url:
                run_applicant_watch(url, ws)
        except Exception as exc:
            log_exception(exc, where="telegram.fragment")

    if not demo_mode and sheet_url:
        applicant_telegram_watch()


@st.cache_data(ttl=60)
def _load(url: str, ws: str, _ver: int) -> pd.DataFrame:
    return load_data(url, ws)


@st.cache_data(ttl=30)
def _load_raw(url: str, ws: str, _ver: int) -> pd.DataFrame:
    return load_data_raw(url, ws, apply_eligibility=False)


def render_unpaid_panel(*, sheet_url: str, ws_name: str, demo_mode: bool) -> None:
    st.markdown("#### 입금 대기")
    st.caption("시트 U열(입금확인) 체크 전 · 매칭 작업 탭에는 안 보입니다.")
    if demo_mode:
        st.info("데모 모드 — 실제 시트 연동 후 목록이 표시됩니다.")
        return
    if not sheet_url:
        st.warning("시트 URL을 입력하세요.")
        return
    try:
        raw = _load_raw(sheet_url, ws_name, st.session_state["load_ver"])
    except Exception as exc:
        ui_error(exc, where="입금 대기 목록", streamlit_module=st)
        return
    pending = unpaid_applicants(raw)
    if pending.empty:
        st.success("입금 대기 중인 신청이 없습니다.")
        return
    st.markdown(f"**{len(pending)}명** — 시트에서 U열 체크 후 **새로고침**")
    rows = []
    for idx, row in pending.iterrows():
        rows.append(
            {
                "행": int(idx),
                "신청일": str(row.get("ts", "") or "—"),
                "이름": str(row.get("name", "") or "—"),
                "연락처": str(row.get("contact", "") or "—"),
                "직군": str(row.get("job", "") or "—")[:40],
                "지역": str(row.get("region", "") or "—"),
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    if st.button("입금 대기 목록 새로고침", key="unpaid_refresh"):
        _load_raw.clear()
        st.rerun()


def render_apps_script_guide() -> None:
    st.markdown("#### 시트 Apps Script (추천)")
    st.info(
        "**Apps Script는 구글 시트에서만 설정합니다.** "
        "Streamlit **Reboot·배포와 무관** — 시트에 코드 붙이고 트리거만 추가하면 됩니다."
    )
    st.markdown(
        "Streamlit 앱은 **새 행**만 (~2분, 앱 켜져 있을 때). "
        "**입금 체크(U열)**·**폼 제출 즉시 알림**은 Apps Script가 담당합니다."
    )
    with st.expander("📋 Apps Script 3단계", expanded=True):
        st.markdown(
            "**1.** `setupTelegram` → token · chat_id  \n"
            "**2.** `installTriggers` ★ — 즉시 알림 + **매일 12시 입금대기**  \n"
            "**3.** `testTelegramPing` · `testUnpaidDigest` (묶음 테스트)"
        )
        st.caption(
            "입금대기 묶음: U열 미체크 + 신청 **3시간+** 지난 사람만 · "
            "시간 변경은 Code.gs 상단 `DIGEST_HOUR` · `UNPAID_MIN_HOURS`"
        )
    gs_path = ROOT / "docs" / "apps-script" / "Code.gs"
    if gs_path.is_file():
        st.download_button(
            "Code.gs 다운로드",
            data=gs_path.read_text(encoding="utf-8"),
            file_name="Code.gs",
            mime="text/plain",
            key="dl_apps_script",
        )


def get_df() -> pd.DataFrame:
    source = expected_data_source(demo_mode=demo_mode, sheet_url=sheet_url)
    cached = st.session_state.get("df")
    if not should_reload_df(
        cached=cached,
        demo_mode=demo_mode,
        data_source=st.session_state.get("_df_source"),
        expected_source=source,
    ):
        return ensure_search_index(cached)

    if demo_mode:
        df = load_demo_data()
    elif sheet_url:
        try:
            df = _load(sheet_url, ws_name, st.session_state["load_ver"])
        except Exception as e:
            ui_error(e, where="시트 로드", streamlit_module=st)
            return pd.DataFrame()
    else:
        return pd.DataFrame()

    st.session_state["_df_source"] = source
    st.session_state["df"] = ensure_search_index(df)
    return st.session_state["df"]


def is_matched(row) -> bool:
    return str(row.get("matched", "")).strip().upper() == "TRUE"


def is_closed(row) -> bool:
    return parse_reject(row.get("reject", 0)) >= 2


def is_rejected(row) -> bool:
    return parse_reject(row.get("reject", 0)) == 1 and not is_matched(row)


def chip(row) -> str:
    if is_matched(row):
        return '<span class="chip chip-g">완료</span>'
    if is_closed(row):
        return '<span class="chip chip-r">종료</span>'
    if parse_reject(row.get("reject", 0)) == 1:
        return '<span class="chip chip-w">거절1</span>'
    return '<span class="chip">대기</span>'


def sjob(j: str) -> str:
    return str(j or "").split("/")[0].strip()[:14]


def syears(y: str) -> str:
    return str(y or "").replace("연차 ", "")


def parse_dday(val) -> int:
    """D-14 → 14. 값이 없으면 맨 뒤."""
    s = str(val or "").strip().upper()
    m = re.search(r"D\s*-?\s*(\d+)", s)
    return int(m.group(1)) if m else 9999


def sort_list_df(frame: pd.DataFrame, sort_by: str) -> pd.DataFrame:
    if frame.empty or "dday" not in frame.columns:
        return frame
    if sort_by == "D-day 임박순":
        return frame.assign(_d=frame["dday"].map(parse_dday)).sort_values("_d", kind="stable").drop(columns="_d")
    if sort_by == "D-day 여유순":
        return (
            frame.assign(_d=frame["dday"].map(parse_dday))
            .sort_values("_d", ascending=False, kind="stable")
            .drop(columns="_d")
        )
    if sort_by == "이름순":
        return frame.sort_values("name", kind="stable")
    return frame


def render_search_bar(
    key: str,
    placeholder: str,
    *,
    label: str = "검색",
    show_hint: bool = True,
) -> str:
    """검색 입력 + ✕ 지우기."""
    st.markdown('<span class="search-bar-anchor"></span>', unsafe_allow_html=True)
    c_input, c_clear = st.columns([15, 1], gap="small")
    with c_input:
        q = st.text_input(label, placeholder=placeholder, label_visibility="collapsed", key=key)
    with c_clear:
        has_text = bool(str(st.session_state.get(key, "")).strip())
        if st.button(
            "✕",
            key=f"{key}_x",
            disabled=not has_text,
            help="검색 지우기",
            use_container_width=True,
        ):
            st.session_state[key] = ""
            st.rerun()
    q = str(q or "").strip()
    if show_hint and q:
        st.markdown(
            f'<p class="search-live-hint">검색 중: <b>{html_lib.escape(q)}</b></p>',
            unsafe_allow_html=True,
        )
    return q


def render_field_filter_panel(frame: pd.DataFrame) -> None:
    """설문 필드별 multiselect 필터."""
    sel = collect_filter_selections()
    chip = st.session_state.get("chip_filter")
    n = sum(len(v) for v in sel.values()) + (1 if chip else 0)
    title = f"상세 필터 · {n}개 적용" if n else "상세 필터"

    with st.expander(title, expanded=n > 0):
        row1 = st.columns(4)
        row2 = st.columns(4)
        row3 = st.columns(2)
        rows = [row1, row2, row3]
        slots = [4, 4, 2]
        idx = 0
        for ri, (cols, width) in enumerate(zip(rows, slots)):
            for ci in range(width):
                if idx >= len(FILTER_FIELDS):
                    break
                key, label = FILTER_FIELDS[idx]
                with cols[ci]:
                    opts = field_options(frame, key)
                    if opts:
                        st.multiselect(
                            label,
                            opts,
                            format_func=lambda v, k=key: option_label(k, v),
                            key=f"flt_{key}",
                            placeholder="전체",
                        )
                idx += 1

        _, btn = st.columns([5, 1])
        with btn:
            st.markdown('<div class="filter-clear-row">', unsafe_allow_html=True)
            if st.button("필터 초기화", key="flt_clr", use_container_width=True):
                clear_all_filters()
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)


def render_active_filter_bar(selections: dict[str, list[str]], chip: dict | None) -> None:
    chips = active_filter_labels(selections)
    if chip:
        chips.append(f'키워드: {chip.get("label", "")}')
    if not chips:
        return
    parts = "".join(
        f'<span class="flt-chip{" flt-chip-kw" if c.startswith("키워드") else ""}">{html_lib.escape(c)}</span>'
        for c in chips
    )
    st.markdown(f'<div class="active-filters">{parts}</div>', unsafe_allow_html=True)
    st.markdown('<div class="active-filter-actions">', unsafe_allow_html=True)
    if st.button("필터 해제", key="flt_bar_clr", use_container_width=False):
        clear_all_filters()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def fmt_contact(c) -> str:
    s = str(c or "").strip().replace("-", "").replace(" ", "")
    if len(s) == 11 and s.isdigit():
        return f"{s[:3]}-{s[3:7]}-{s[7:]}"
    return str(c or "—")


def trunc(text: str, n: int = 72) -> str:
    s = str(text or "—").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def collect_matched_pairs(frame: pd.DataFrame) -> list[dict]:
    """완료 매칭 쌍 수집 (중복 제거)."""
    pairs: list[dict] = []
    seen: set[frozenset] = set()
    name_to_idx = {str(r["name"]): idx for idx, r in frame.iterrows()}
    matched = frame[frame["matched"].astype(str).str.upper().eq("TRUE")]

    for idx_a, row_a in matched.iterrows():
        na = str(row_a.get("name", ""))
        nb = str(row_a.get("matched_w", "")).strip()
        key = frozenset([na, nb]) if nb else frozenset([na])
        if key in seen:
            continue
        seen.add(key)

        idx_b = name_to_idx.get(nb)
        row_b = frame.loc[idx_b] if idx_b is not None else None
        vm = None
        score, mutual, kws = 0, False, []
        if row_b is not None:
            ev = evaluate(row_a, row_b)
            score, mutual, kws = ev.score, ev.mutual, ev.keywords
            vm = ev.value

        pairs.append({
            "idx_a": idx_a, "idx_b": idx_b,
            "name_a": na, "name_b": nb or "?",
            "row_a": row_a, "row_b": row_b,
            "score": score, "mutual": mutual, "keywords": kws,
            "value": vm,
            "ts": str(row_a.get("ts", "")),
            "matched_at": format_matched_at(row_a.get("matched_at"))
            or (format_matched_at(row_b.get("matched_at")) if row_b is not None else ""),
        })
    pairs.sort(key=lambda p: p.get("matched_at") or p["ts"], reverse=True)
    return pairs


def filter_pairs(pairs: list[dict], query: str) -> list[dict]:
    q = query.strip().lower()
    if not q:
        return pairs
    out = []
    for p in pairs:
        blob = " ".join([
            p["name_a"], p["name_b"],
            str(p["row_a"].get("job", "")), str(p["row_a"].get("region", "")),
            str(p["row_a"].get("contact", "")),
            str(p["row_b"].get("job", "") if p["row_b"] is not None else ""),
            str(p["row_b"].get("region", "") if p["row_b"] is not None else ""),
            str(p["row_b"].get("contact", "") if p["row_b"] is not None else ""),
        ]).lower()
        if q in blob:
            out.append(p)
    return out


def person_done_html(row, missing_name: str = "") -> str:
    if row is None:
        nm = html_lib.escape(missing_name or "?")
        return (
            f'<div class="done-person missing">'
            f'<div class="done-pname">{nm}</div>'
            f'<div class="done-pmeta">시트에 상대 데이터 없음</div></div>'
        )
    want = html_lib.escape(str(row.get("want", "")))
    have = html_lib.escape(str(row.get("have", "")))
    return (
        f'<div class="done-person">'
        f'<div class="done-pname">{html_lib.escape(str(row.get("name", "")))}</div>'
        f'<div class="done-pmeta">'
        f'{html_lib.escape(sjob(row.get("job", "")))} · {html_lib.escape(str(row.get("region", "")))} · '
        f'{html_lib.escape(syears(row.get("years", "")))}'
        f'</div>'
        f'<div class="done-contact">{html_lib.escape(fmt_contact(row.get("contact", "")))}</div>'
        f'<div class="done-lbl">원하는 것</div>'
        f'<div class="done-txt" title="{want}">{trunc(want)}</div>'
        f'<div class="done-lbl">제공 가치</div>'
        f'<div class="done-txt" title="{have}">{trunc(have)}</div>'
        f'</div>'
    )


def render_done_card(pair: dict) -> str:
    vm = pair.get("value")
    badge = value_badge_html(vm) if vm else ""
    story = story_block_html(vm) if vm else ""
    kw_html = keywords_html(pair["keywords"]) if pair["keywords"] else ""
    kw_block = f'<div class="done-kws">{kw_html}</div>' if kw_html else ""
    ma = html_lib.escape(pair.get("matched_at", ""))
    date_line = f'<div class="done-date">매칭일 {ma}</div>' if ma else ""
    return (
        f'<div class="done-card">'
        f'<div class="done-head">'
        f'<span class="done-names">{html_lib.escape(pair["name_a"])}'
        f'<span class="link-icon">↔</span>{html_lib.escape(pair["name_b"])}</span>'
        f'<span class="done-score">{badge}</span>'
        f'</div>{date_line}{story}'
        f'<div class="done-body">'
        f'{person_done_html(pair["row_a"])}'
        f'{person_done_html(pair["row_b"], pair["name_b"])}'
        f'</div>{kw_block}</div>'
    )


def do_match(a: int, b: int) -> None:
    df = st.session_state["df"]
    na, nb = df.loc[a, "name"], df.loc[b, "name"]
    at = now_matched_at()
    if not demo_mode:
        set_matched(sheet_url, a, nb, at, ws_name)
        set_matched(sheet_url, b, na, at, ws_name)
    df.loc[a, "matched"], df.loc[a, "matched_w"], df.loc[a, "matched_at"] = "TRUE", nb, at
    df.loc[b, "matched"], df.loc[b, "matched_w"], df.loc[b, "matched_at"] = "TRUE", na, at
    st.session_state["df"] = df
    _refresh_df_index()
    st.session_state["flash"] = f"{na} ↔ {nb} 매칭 완료 ({at})"
    st.session_state["selected"] = []


def toggle_select(idx: int) -> None:
    sel: list = list(st.session_state.get("selected", []))
    if idx in sel:
        sel.remove(idx)
    elif len(sel) < 2:
        sel.append(idx)
    else:
        sel[1] = idx  # 2명 선택 중이면 두 번째 슬롯 교체
    st.session_state["selected"] = sel
    if sel:
        st.session_state["mob_view"] = "detail"


def render_mobile_action_bar(has_selection: bool) -> None:
    """상단 — 계정 · 설정 · 목록/상세 · 새로고침."""
    st.markdown('<span class="mob-action-bar-anchor"></span>', unsafe_allow_html=True)
    if has_selection:
        c_user, c_set, c_list, c_view, c_ref = st.columns([2.2, 0.65, 1, 1, 0.65], gap="small")
    else:
        c_user, c_set, c_ref = st.columns([3.5, 1.2, 0.65], gap="small")
        c_list = c_view = None

    with c_user:
        st.markdown(
            f'<p class="mob-user"><span class="mob-user-lbl">접속</span>{html_lib.escape(str(current_user() or ""))}</p>',
            unsafe_allow_html=True,
        )
    with c_set:
        if st.button(
            "설정",
            key="mob_settings",
            help="설정 · 텔레그램 (설정·알림 탭)",
            use_container_width=True,
            type="primary" if st.session_state.get("focus_settings") else "secondary",
        ):
            st.session_state["focus_settings"] = True
            st.rerun()
    if has_selection and c_list is not None and c_view is not None:
        view = st.session_state.get("mob_view", "detail")
        with c_list:
            if st.button(
                "목록",
                key="mob_go_list",
                use_container_width=True,
                type="primary" if view == "list" else "secondary",
            ):
                st.session_state["mob_view"] = "list"
                st.rerun()
        with c_view:
            lbl = "비교" if len(st.session_state.get("selected", [])) >= 2 else "상세"
            if st.button(
                lbl,
                key="mob_go_detail",
                use_container_width=True,
                type="primary" if view == "detail" else "secondary",
            ):
                st.session_state["mob_view"] = "detail"
                st.rerun()
    with c_ref:
        if st.button("↻", key="mob_refresh", help="새로고침", use_container_width=True):
            _refresh_data()
            st.rerun()


def render_compare_panel(a: int, b: int) -> None:
    """2명 비교 — 요약 + 탭으로 프로필 전환."""
    ra, rb = df.loc[a], df.loc[b]
    pair = evaluate(ra, rb)
    vm = pair.value
    kws_ab = analyze_pair(ra, rb)
    kws_ba = analyze_pair(rb, ra)
    badge = value_badge_html(vm) if vm else ""
    na = html_lib.escape(str(ra.get("name", "")))
    nb = html_lib.escape(str(rb.get("name", "")))

    st.markdown(
        f'<div class="compare-hero">'
        f'<div class="compare-names">{na} <span class="cmp-vs">↔</span> {nb}</div>'
        f'<div class="compare-value">{badge}'
        f'<span class="compare-score">{score_label(pair.score, pair.mutual)}</span></div>'
        f"</div>",
        unsafe_allow_html=True,
    )
    if vm:
        st.markdown(story_block_html(vm), unsafe_allow_html=True)

    st.markdown('<div class="compare-kw-block">', unsafe_allow_html=True)

    st.markdown(
        f'<div class="compare-section">'
        f'<div class="compare-section-title">'
        f'<span class="compare-section-who">{na}</span>'
        f'<span class="compare-section-arrow">→</span>'
        f'<span class="compare-section-who">{nb}</span>'
        f'<span class="compare-section-sub">기준 일치</span>'
        f"</div>",
        unsafe_allow_html=True,
    )
    render_match_keywords(kws_ab, f"cmp{a}{b}", clickable=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        f'<div class="compare-section compare-section-gap">'
        f'<div class="compare-section-title">'
        f'<span class="compare-section-who">{nb}</span>'
        f'<span class="compare-section-arrow">→</span>'
        f'<span class="compare-section-who">{na}</span>'
        f'<span class="compare-section-sub">기준 일치</span>'
        f"</div>",
        unsafe_allow_html=True,
    )
    render_match_keywords(kws_ba, f"cmp{b}{a}", clickable=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

    can_match = (
        not is_matched(ra) and not is_closed(ra)
        and not is_matched(rb) and not is_closed(rb)
    )
    if can_match:
        st.markdown('<div class="compare-match-row">', unsafe_allow_html=True)
        if st.button(
            f"{ra['name']} ↔ {rb['name']} 매칭 확정",
            type="primary",
            use_container_width=True,
            key=f"match_{a}_{b}",
        ):
            do_match(a, b)
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="compare-tabs-wrap">', unsafe_allow_html=True)
    tab_a, tab_b = st.tabs([f"① {ra['name']}", f"② {rb['name']}"])
    with tab_a:
        render_person(a, 1, show_recommend=False)
    with tab_b:
        render_person(b, 2, show_recommend=False)
    st.markdown("</div>", unsafe_allow_html=True)


def _refresh_df_index() -> None:
    st.session_state["df"] = ensure_search_index(drop_search_index(st.session_state["df"]))


def filter_by_status(frame: pd.DataFrame, status: str) -> pd.DataFrame:
    """상태 필터 — 대기 / 거절 / 완료 / 종료."""
    if status == "대기":
        return frame[
            ~frame["matched"].astype(str).str.upper().eq("TRUE")
            & frame["reject"].apply(parse_reject).eq(0)
        ]
    if status == "거절":
        return frame[
            ~frame["matched"].astype(str).str.upper().eq("TRUE")
            & frame["reject"].apply(parse_reject).eq(1)
        ]
    if status == "완료":
        return frame[frame["matched"].astype(str).str.upper().eq("TRUE")]
    if status == "종료":
        return frame[frame["reject"].apply(parse_reject).ge(2)]
    return frame


def build_list_blocks(frame: pd.DataFrame) -> list[tuple]:
    """완료 매칭은 상대와 한 덩어리로 묶음."""
    name_to_idx = {str(frame.loc[i, "name"]).strip(): i for i in frame.index}
    seen: set = set()
    blocks: list[tuple] = []
    for idx in frame.index:
        if idx in seen:
            continue
        row = frame.loc[idx]
        if is_matched(row):
            partner = str(row.get("matched_w", "")).strip()
            pidx = name_to_idx.get(partner)
            if pidx is not None and pidx in frame.index and pidx not in seen:
                seen.add(idx)
                seen.add(pidx)
                blocks.append(("pair", idx, pidx))
                continue
        seen.add(idx)
        blocks.append(("single", idx))
    return blocks


def _list_row_meta_html(row, *, in_pair: bool = False) -> str:
    region = html_lib.escape(str(row.get("region", "")))
    job = html_lib.escape(sjob(row.get("job", "")))
    dday = html_lib.escape(str(row.get("dday", "")))
    status = "" if (in_pair and is_matched(row)) else chip(row)
    return (
        f'<div class="list-row-inner">'
        f'<div class="list-row-tags">{status}'
        f'<span class="chip chip-r">{dday}</span></div>'
        f'<div class="list-row-meta">{region} · {job}</div>'
        f"</div>"
    )


def _render_list_row_content(idx: int, row, selected: list, *, in_pair: bool = False) -> None:
    nm = str(row.get("name", ""))
    prefix = ""
    if idx in selected:
        prefix = "① " if selected.index(idx) == 0 else "② "

    if st.button(f"{prefix}{nm}", key=f"p{idx}", use_container_width=True):
        toggle_select(idx)
        st.rerun()
    st.markdown(_list_row_meta_html(row, in_pair=in_pair), unsafe_allow_html=True)


def render_list_row(idx: int, row, selected: list) -> None:
    """목록 카드 — 이름 + 상태/D-day/메타 (테두리 안)."""
    with st.container(border=True):
        if idx in selected:
            n = selected.index(idx) + 1
            st.markdown(f'<div class="sel-bar sel-{n}"></div>', unsafe_allow_html=True)
        _render_list_row_content(idx, row, selected)


def render_match_pair(idx_a: int, idx_b: int, row_a, row_b, selected: list) -> None:
    """매칭 완료 2명을 한 테두리로 묶음."""
    na = html_lib.escape(str(row_a.get("name", "")))
    nb = html_lib.escape(str(row_b.get("name", "")))
    ma = format_matched_at(row_a.get("matched_at")) or format_matched_at(row_b.get("matched_at"))
    date_chip = (
        f'<span class="chip chip-date">{html_lib.escape(ma)}</span>' if ma else ""
    )
    with st.container(border=True):
        st.markdown(
            f'<div class="pair-head"><span class="chip chip-g">완료</span>'
            f'{date_chip}'
            f'<span class="pair-names">{na} ↔ {nb}</span></div>',
            unsafe_allow_html=True,
        )
        _render_list_row_content(idx_a, row_a, selected, in_pair=True)
        st.markdown('<div class="pair-divider"></div>', unsafe_allow_html=True)
        _render_list_row_content(idx_b, row_b, selected, in_pair=True)


def render_match_keywords(
    kws: list[MatchKeyword], prefix: str, clickable: bool = True, show_chips: bool = True
) -> None:
    """일치 항목 키워드 — 컴팩트 필터 pill."""
    if show_chips:
        st.markdown(f'<div class="rec-kw">{keywords_html(kws)}</div>', unsafe_allow_html=True)
    if not clickable:
        return
    matched = [k for k in kws if k.matched and k.keyword not in ("—", "")]
    if not matched:
        return
    for chunk_start in range(0, len(matched), 4):
        chunk = matched[chunk_start : chunk_start + 4]
        cols = st.columns(len(chunk))
        for i, kw in enumerate(chunk):
            with cols[i]:
                if st.button(
                    kw.label,
                    key=f"kw{prefix}{kw.key}{chunk_start + i}",
                    use_container_width=True,
                ):
                    st.session_state["chip_filter"] = {
                        "field": kw.filter_field,
                        "value": kw.filter_value,
                        "label": f"{kw.label}: {kw.keyword}",
                    }
                    st.rerun()


def _meta_item(label: str, value: str) -> str:
    v = html_lib.escape(str(value or "—"))
    return (
        f'<div class="meta-item"><span class="meta-lbl">{html_lib.escape(label)}</span>'
        f'<span class="meta-val">{v}</span></div>'
    )


def profile_hero_html(row) -> str:
    dday = html_lib.escape(str(row.get("dday", "")))
    contact = html_lib.escape(fmt_contact(row.get("contact", "")))
    extra_chips = ""
    if is_matched(row):
        ma = format_matched_at(row.get("matched_at"))
        if ma:
            extra_chips += f'<span class="chip chip-date">{html_lib.escape(ma)}</span>'
        partner = str(row.get("matched_w", "")).strip()
        if partner:
            extra_chips += f'<span class="chip chip-g">↔ {html_lib.escape(partner)}</span>'
    chips = (
        f'<div class="profile-chips">{chip(row)}{extra_chips}'
        f'<span class="chip">{html_lib.escape(str(row.get("gender", "")))}</span>'
        f'<span class="chip">{html_lib.escape(str(row.get("region", "")))}</span>'
        f'<span class="chip">{html_lib.escape(sjob(row.get("job", "")))}</span>'
        f'<span class="chip">{html_lib.escape(syears(row.get("years", "")))}</span>'
        f"</div>"
    )
    return (
        f'<div class="profile-hero">'
        f'<div class="profile-top">'
        f'<div><h2 class="profile-name">{html_lib.escape(str(row.get("name", "")))}</h2>'
        f'<div class="profile-contact">{contact}</div></div>'
        f'<span class="dday-badge">{dday}</span></div>'
        f"{chips}</div>"
    )


def profile_sections_html(row) -> str:
    want_txt = html_lib.escape(str(row.get("want", "—")))
    have_txt = html_lib.escape(str(row.get("have", "—")))
    return (
        f'<div class="section-card want">'
        f'<div class="section-title"><span class="ico">□</span> 원하는 것 요약</div>'
        f'<div class="meta-grid">'
        f'{_meta_item("희망 직군", sjob(str(row.get("w_job", ""))))}'
        f'{_meta_item("희망 지역", row.get("w_region", "무관"))}'
        f'{_meta_item("희망 연차", row.get("w_years", "무관"))}'
        f'{_meta_item("희망 성별", row.get("w_gender", "무관"))}'
        f'{_meta_item("협업 깊이", _theme(str(row.get("depth", ""))))}'
        f'{_meta_item("가치관", _theme(str(row.get("values", ""))))}'
        f"</div>"
        f'<div class="text-block"><span class="meta-lbl">원하는 것</span>'
        f'<p class="text-body">{want_txt}</p></div></div>'
        f'<div class="section-card have">'
        f'<div class="section-title have-ico"><span class="ico">◇</span> 제공 가치</div>'
        f'<p class="text-body">{have_txt}</p></div>'
    )


def _rec_meta_html(row) -> str:
    parts = [
        str(row.get("region", "")),
        sjob(str(row.get("job", ""))),
        syears(str(row.get("years", ""))),
        str(row.get("gender", "")),
    ]
    return "".join(
        f'<span class="rec-meta-chip">{html_lib.escape(p)}</span>'
        for p in parts
        if p and p.strip() and p.strip() != "—"
    )


def render_detail_toolbar(idx: int, slot: int, *, include_back: bool = False) -> None:
    """프로필 상단 — 목록 · 라벨 · 거절 · 닫기 한 줄."""
    row = df.loc[idx]
    tag = "①" if slot == 1 else "②"
    can_reject = not is_matched(row) and not is_closed(row)

    st.markdown('<span class="detail-toolbar-anchor"></span>', unsafe_allow_html=True)
    if include_back:
        c_back, c_lbl, c_rej, c_close = st.columns([1.4, 4.2, 1.1, 1.1], gap="small")
        with c_back:
            if st.button("← 목록", key=f"back_{idx}_{slot}", use_container_width=True):
                st.session_state["selected"] = []
                st.session_state["mob_view"] = "list"
                st.rerun()
    else:
        c_lbl, c_rej, c_close = st.columns([5.6, 1.1, 1.1], gap="small")

    with c_lbl:
        st.markdown(
            f'<p class="detail-toolbar-title">'
            f'<span class="slot-tag slot-{slot}">{tag}</span> 프로필</p>',
            unsafe_allow_html=True,
        )
    with c_rej:
        if can_reject:
            if st.button("거절", key=f"r{idx}s{slot}", use_container_width=True):
                do_reject(idx)
                st.rerun()
    with c_close:
        if st.button("닫기", key=f"x{idx}s{slot}", use_container_width=True):
            sel = [i for i in st.session_state.get("selected", []) if i != idx]
            st.session_state["selected"] = sel
            if not sel:
                st.session_state["mob_view"] = "list"
            st.rerun()


def render_person(idx: int, slot: int, show_recommend: bool = True, *, include_back: bool = False) -> None:
    row = df.loc[idx]

    st.markdown('<div class="detail-panel">', unsafe_allow_html=True)
    render_detail_toolbar(idx, slot, include_back=include_back)

    st.markdown(profile_hero_html(row), unsafe_allow_html=True)

    if is_matched(row):
        ma = format_matched_at(row.get("matched_at"))
        partner = str(row.get("matched_w", "")).strip()
        msg = f"매칭 완료 — {partner}" if partner else "매칭 완료"
        if ma:
            msg += f" · {ma}"
        st.success(msg)
    elif is_closed(row):
        st.error("매칭 종료 (거절 2회)")

    st.markdown(profile_sections_html(row), unsafe_allow_html=True)
    render_profile_editor(idx, slot)

    if show_recommend and not is_matched(row) and not is_closed(row):
        st.markdown('<div class="rec-section-title">추천 상대</div>', unsafe_allow_html=True)
        for rank, cand in enumerate(recommend(idx, df, 3), 1):
            cr = df.loc[cand.idx]
            cn = str(cr.get("name", ""))
            vm = cand.value
            if vm:
                st.markdown(
                    recommendation_card_html(
                        cn, vm, rank, keywords_html(cand.keywords), _rec_meta_html(cr)
                    ),
                    unsafe_allow_html=True,
                )
            render_match_keywords(cand.keywords, f"r{idx}{cand.idx}", clickable=True, show_chips=False)
            st.markdown('<div class="rec-btn-row">', unsafe_allow_html=True)
            if st.button("매칭 확정", key=f"m{idx}{cand.idx}s{slot}", type="primary", use_container_width=True):
                do_match(idx, cand.idx)
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def do_reject(i: int) -> None:
    df = st.session_state["df"]
    cur = parse_reject(df.loc[i, "reject"])
    df.loc[i, "reject"] = increment_reject(sheet_url, i, cur, ws_name) if not demo_mode else cur + 1
    st.session_state["df"] = df
    _refresh_df_index()


def save_profile(idx: int, updates: dict[str, object]) -> None:
    """앱 편집 → session_state + 구글 시트 반영."""
    frame = st.session_state["df"]
    for key, val in updates.items():
        frame.loc[idx, key] = val
    if str(updates.get("matched", "")).strip().upper() != "TRUE":
        frame.loc[idx, "matched_w"] = ""
        frame.loc[idx, "matched_at"] = ""
    elif not str(frame.loc[idx, "matched_at"] or "").strip():
        frame.loc[idx, "matched_at"] = now_matched_at()
    st.session_state["df"] = frame
    _refresh_df_index()
    if not demo_mode and sheet_url:
        sheet_fields = dict(updates)
        if str(updates.get("matched", "")).strip().upper() == "TRUE":
            sheet_fields["matched_at"] = frame.loc[idx, "matched_at"]
        else:
            sheet_fields["matched_at"] = ""
        update_profile_fields(sheet_url, idx, sheet_fields, ws_name)


def _cell_str(row, key: str) -> str:
    v = row.get(key, "")
    if pd.isna(v):
        return ""
    return str(v)


def render_profile_editor(idx: int, slot: int) -> None:
    """프로필 필드 편집 — 저장 시 구글 시트에 반영."""
    row = df.loc[idx]
    with st.expander("프로필 편집", expanded=False):
        with st.form(f"edit_{idx}_{slot}"):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input(EDIT_LABELS["name"], _cell_str(row, "name"))
                gender = st.text_input(EDIT_LABELS["gender"], _cell_str(row, "gender"))
                contact = st.text_input(EDIT_LABELS["contact"], _cell_str(row, "contact"))
                job = st.text_input(EDIT_LABELS["job"], _cell_str(row, "job"))
                region = st.text_input(EDIT_LABELS["region"], _cell_str(row, "region"))
                years = st.text_input(EDIT_LABELS["years"], _cell_str(row, "years"))
                dday = st.text_input(EDIT_LABELS["dday"], _cell_str(row, "dday"))
            with c2:
                w_job = st.text_input(EDIT_LABELS["w_job"], _cell_str(row, "w_job"))
                w_region = st.text_input(EDIT_LABELS["w_region"], _cell_str(row, "w_region"))
                w_gender = st.text_input(EDIT_LABELS["w_gender"], _cell_str(row, "w_gender"))
                w_years = st.text_input(EDIT_LABELS["w_years"], _cell_str(row, "w_years"))
                depth = st.text_input(EDIT_LABELS["depth"], _cell_str(row, "depth"))
                values = st.text_input(EDIT_LABELS["values"], _cell_str(row, "values"))
                reject_n = st.number_input(
                    EDIT_LABELS["reject"],
                    min_value=0,
                    max_value=99,
                    value=int(parse_reject(row.get("reject", 0))),
                    step=1,
                )
                matched_on = st.checkbox(
                    EDIT_LABELS["matched"],
                    value=is_matched(row),
                )
            have = st.text_area(EDIT_LABELS["have"], _cell_str(row, "have"), height=80)
            want = st.text_area(EDIT_LABELS["want"], _cell_str(row, "want"), height=80)

            if st.form_submit_button("시트에 저장", type="primary", use_container_width=True):
                updates = {
                    "name": name,
                    "gender": gender,
                    "contact": contact,
                    "job": job,
                    "region": region,
                    "years": years,
                    "dday": dday,
                    "w_job": w_job,
                    "w_region": w_region,
                    "w_gender": w_gender,
                    "w_years": w_years,
                    "depth": depth,
                    "values": values,
                    "reject": reject_n,
                    "matched": "TRUE" if matched_on else "",
                    "have": have,
                    "want": want,
                }
                try:
                    save_profile(idx, updates)
                    where = "데모 데이터" if demo_mode else "구글 시트"
                    st.session_state["flash"] = f"{name} 프로필 저장 완료 ({where})"
                    st.rerun()
                except Exception as e:
                    ui_error(e, where="프로필 저장", streamlit_module=st)
        if demo_mode:
            st.caption("데모 모드: 시트에는 반영되지 않고 이 세션에만 저장됩니다.")


df = get_df()
if df.empty:
    if st.session_state.get("demo_mode", True):
        st.warning("데모 데이터를 불러오지 못했습니다. **새로고침**을 눌러 보세요.")
    elif not _saved_sheet_url():
        st.warning(
            "시트 주소가 없습니다. **⚙ 설정**에서 「데모 데이터」를 켜거나 "
            "구글 시트 URL을 입력하세요."
        )
    else:
        st.warning(
            "표시할 신청이 없습니다. 시트에 **입금확인**된 행만 보입니다. "
            "U열(입금확인) 체크 · X열(환불) 미체크인지 확인하세요."
        )
    st.stop()

n = len(df)
m = int(df["matched"].astype(str).str.upper().eq("TRUE").sum())
c = int(df["reject"].apply(parse_reject).ge(2).sum())
r = int((~df["matched"].astype(str).str.upper().eq("TRUE") & df["reject"].apply(parse_reject).eq(1)).sum())
w = int((~df["matched"].astype(str).str.upper().eq("TRUE") & df["reject"].apply(parse_reject).eq(0)).sum())

_logo = logo_data_uri()
render_mobile_action_bar(has_selection=bool(st.session_state.get("selected")))
if st.session_state.get("focus_settings"):
    st.info("**설정 · 알림** 탭에서 데모/시트 연동 · **텔레그램 알림 테스트**를 할 수 있습니다.")
st.markdown(
    f'<div class="topbar">'
    f'<div class="topbar-brand">'
    f'<img class="logo-mark" src="{_logo}" alt="단골팅 로고"/>'
    f'<div class="brand-text"><h1>단골팅 · 프로필 관리</h1>'
    f'<div class="brand-sub">매칭 작업실</div></div>'
    f'</div>'
    f'<div class="stats stats-chips">'
    f'<span class="stat-chip">전체 <b>{n}</b></span>'
    f'<span class="stat-chip wait">대기 <b>{w}</b></span>'
    f'<span class="stat-chip warn">거절 <b>{r}</b></span>'
    f'<span class="stat-chip ok">완료 <b>{m}</b></span>'
    f'<span class="stat-chip end">종료 <b>{c}</b></span>'
    f'<span class="stat-chip {"tg" if telegram_enabled() else "tg-off"}">'
    f'텔레그램 <b>{"ON" if telegram_enabled() else "OFF"}</b></span>'
    f'</div></div>',
    unsafe_allow_html=True,
)
if st.session_state.get("flash"):
    st.success(st.session_state["flash"])
    st.session_state["flash"] = ""

tab1, tab2, tab3, tab4 = st.tabs(["매칭 작업", "완료 목록", "원본 데이터", "설정 · 알림"])

with tab1:
    date_from, date_to = render_global_date_filter(df)

    render_field_filter_panel(df)
    field_sel = collect_filter_selections()
    cf = st.session_state.get("chip_filter")
    render_active_filter_bar(field_sel, cf)

    selected: list = [i for i in st.session_state.get("selected", []) if i in df.index]
    mob_view = st.session_state.get("mob_view", "list" if not selected else "detail")
    if not selected:
        st.session_state["mob_view"] = "list"

    q = render_search_bar(
        "sq",
        "이름 · 직군 · 지역 · 제공가치 · 원하는 것 — 입력 즉시 필터",
    )

    list_marker = ""
    if selected and mob_view == "list":
        list_marker = '<span class="mob-show-list-only"></span>'
    st.markdown('<span class="list-layout-anchor"></span>', unsafe_allow_html=True)
    left, right = st.columns([22, 78], gap="large")

    with left:
        st.markdown(f'<span class="list-panel-col">{list_marker}</span>', unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown('<p class="panel-lbl">상태</p>', unsafe_allow_html=True)
            fs = st.radio(
                "상태",
                ["전체", "대기", "거절", "완료", "종료"],
                horizontal=True,
                label_visibility="collapsed",
                key="fs",
            )
            st.markdown('<p class="panel-lbl sort-lbl">정렬</p>', unsafe_allow_html=True)
            sort_by = st.selectbox(
                "정렬",
                ["D-day 임박순", "D-day 여유순", "이름순", "신청순"],
                index=0,
                label_visibility="collapsed",
                key="list_sort",
            )

            fdf = df.copy()
            fdf = apply_date_filter(fdf, date_from, date_to)
            fdf = filter_by_status(fdf, fs) if fs != "전체" else fdf
            fdf = apply_field_filters(fdf, field_sel)
            fdf = apply_keyword_filter(fdf, cf)
            fdf = search_df(fdf, q)
            if sort_by != "신청순":
                fdf = sort_list_df(fdf, sort_by)

            sel_hint = f" · 선택 {len(selected)}/2" if selected else ""
            st.markdown('<div class="list-divider"></div>', unsafe_allow_html=True)
            st.markdown(f'<p class="list-hdr">{len(fdf)}명{sel_hint}</p>', unsafe_allow_html=True)

            for block in build_list_blocks(fdf):
                if block[0] == "pair":
                    ia, ib = block[1], block[2]
                    render_match_pair(ia, ib, fdf.loc[ia], fdf.loc[ib], selected)
                else:
                    idx = block[1]
                    render_list_row(idx, fdf.loc[idx], selected)

            if selected:
                if st.button("선택 초기화", key="clr_all", use_container_width=True):
                    st.session_state["selected"] = []
                    st.session_state["mob_view"] = "list"
                    st.rerun()

    with right:
        with st.container(border=True):
            if not selected:
                st.markdown(
                    '<p class="empty-hint">목록에서 1~2명을 선택하세요.<br>'
                    '2명 선택 시 비교 탭에서 나란히 확인할 수 있습니다.</p>',
                    unsafe_allow_html=True,
                )
            elif len(selected) == 1:
                if mob_view == "detail":
                    st.markdown('<span class="mob-detail-open"></span>', unsafe_allow_html=True)
                render_person(selected[0], 1, show_recommend=True, include_back=True)
                st.caption("한 명 더 선택하면 비교 화면이 열립니다.")
            else:
                if mob_view == "detail":
                    st.markdown('<span class="mob-detail-open"></span>', unsafe_allow_html=True)
                render_compare_panel(selected[0], selected[1])

with tab2:
    pairs = collect_matched_pairs(df)
    st.markdown(
        f'<div class="done-toolbar">'
        f'<span class="done-count">완료 매칭 <b>{len(pairs)}</b>쌍</span></div>',
        unsafe_allow_html=True,
    )
    q_done = st.text_input(
        "완료 검색",
        placeholder="이름 · 직군 · 지역 · 연락처 검색",
        label_visibility="collapsed",
        key="done_q",
    )
    pairs = filter_pairs(pairs, q_done)

    if not pairs:
        st.markdown(
            '<p class="done-empty">완료된 매칭이 없습니다.</p>',
            unsafe_allow_html=True,
        )
    else:
        cards = "".join(render_done_card(p) for p in pairs)
        st.markdown(f'<div class="done-grid">{cards}</div>', unsafe_allow_html=True)

with tab3:
    labels = {
        "name": "성함", "gender": "성별", "job": "직군", "region": "지역",
        "have": "제공가치", "want": "원하는것", "matched": "매칭여부",
        "reject": "거절횟수", "dday": "D-day",
    }
    cols = [c for c in labels if c in df.columns]
    st.dataframe(df[cols].rename(columns=labels), use_container_width=True, height=320)

with tab4:
    st.markdown("#### 연동 · 알림")
    st.caption(
        "왼쪽 Streamlit 사이드바가 안 보이면 **화면 왼쪽 가장자리 ▶** 를 눌러 펼치세요. "
        "아래 설정은 사이드바와 동일합니다."
    )
    render_settings_panel(key_prefix="tab_")
    st.divider()
    render_unpaid_panel(sheet_url=sheet_url, ws_name=ws_name, demo_mode=demo_mode)
    st.divider()
    render_apps_script_guide()
