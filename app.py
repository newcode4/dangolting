"""
단골팅 관리자 — 매칭 작업실
"""
from __future__ import annotations

import html as html_lib
import re
from pathlib import Path
from urllib.parse import quote

import streamlit as st
import pandas as pd

from utils.matching import recommend, score_label, evaluate
from utils.value_match import story_block_html, value_badge_html
from utils.match_display import keywords_html, apply_keyword_filter, MatchKeyword, analyze_pair, _theme
from utils.columns import DEFAULT_SHEET_URL, DEFAULT_WORKSHEET, parse_reject
from utils.sheets import load_data, load_demo_data, set_matched, increment_reject
from utils.filters import (
    FILTER_FIELDS,
    field_options,
    option_label,
    collect_filter_selections,
    apply_field_filters,
    active_filter_labels,
    clear_all_filters,
)

ROOT = Path(__file__).resolve().parent
LOGO = ROOT / "assets" / "logo-mark.svg"

G = "10px"  # 내부 간격
PANEL = "14px"  # 패널 안쪽 여백
SPACE = "20px"  # 상세 화면 여백


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


st.set_page_config(
    page_title="단골팅",
    page_icon=str(LOGO),
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    f"""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
html,body,[class*="css"]{{font-family:Pretendard,-apple-system,sans-serif;-webkit-text-size-adjust:100%}}

header[data-testid="stHeader"]{{
  background:rgba(20,20,24,.96)!important;border-bottom:1px solid rgba(128,128,128,.12);
}}
section.main > div.block-container{{
  padding:1.25rem 2rem 2rem!important;max-width:1280px;
}}
[data-testid="stToolbar"]{{display:none}}
footer{{visibility:hidden;height:0}}

/* Streamlit 기본 간격 */
[data-testid="stVerticalBlock"] > div{{gap:{G}!important}}
div[data-testid="stButton"]{{margin:0!important}}
div[data-testid="stButton"] > button{{
  padding:5px 12px!important;min-height:32px!important;font-size:.8rem!important;
  border-radius:6px!important;
}}
div[data-testid="stButton"] > button[kind="primary"]{{
  min-height:32px!important;padding:5px 14px!important;
}}
[data-testid="stTextInput"] input{{min-height:34px!important;font-size:.85rem!important;padding:6px 10px!important}}
[data-testid="stRadio"] label{{font-size:.76rem!important;padding:3px 8px!important;min-height:28px!important}}
.stTabs [data-baseweb="tab"]{{padding:6px 12px!important;font-size:.82rem!important;min-height:32px!important}}

/* ── 작업 영역 2열 ── */
div[data-testid="stHorizontalBlock"]{{gap:20px!important;align-items:flex-start!important}}
div[data-testid="stHorizontalBlock"] > [data-testid="column"]:first-child{{
  flex:0 0 252px!important;max-width:252px!important;
}}
div[data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child{{
  flex:1 1 auto!important;min-width:0!important;
}}

/* 패널 박스 */
[data-testid="stVerticalBlockBorderWrapper"]{{
  padding:{PANEL}!important;border-radius:10px!important;
  background:rgba(255,255,255,.02)!important;
  border:1px solid rgba(128,128,128,.14)!important;
}}
div[data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child [data-testid="stVerticalBlockBorderWrapper"]{{
  padding:{PANEL} 18px {PANEL} 18px!important;
}}

.topbar{{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:12px;flex-wrap:wrap}}
.topbar-brand{{display:flex;align-items:center;gap:10px;min-width:0}}
.logo-mark{{width:38px;height:38px;flex-shrink:0;display:block}}
.brand-text h1{{font-size:1.12rem;font-weight:700;margin:0;line-height:1.2}}
.brand-sub{{font-size:.68rem;color:#888;font-weight:500;margin-top:1px}}
.stats{{font-size:.76rem;color:#888;text-align:right}}
.stats b{{font-weight:600;color:#ccc}}
.sidebar-brand{{
  display:flex;align-items:center;gap:8px;margin:-4px 0 10px;padding-bottom:10px;
  border-bottom:1px solid rgba(128,128,128,.14);
}}
.sidebar-brand img{{width:28px;height:28px;flex-shrink:0}}
.sidebar-brand span{{font-size:.92rem;font-weight:700;letter-spacing:-.02em}}

/* ── 왼쪽 목록: 컴팩트 행 ── */
.list-hdr{{font-size:.72rem;color:#888;margin:0 0 8px}}
div[data-testid="stHorizontalBlock"] > [data-testid="column"]:first-child [data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stButton"] > button{{
  min-height:28px!important;padding:3px 6px!important;
  font-size:.78rem!important;font-weight:600!important;text-align:left!important;
  border:1px solid rgba(128,128,128,.12)!important;background:rgba(128,128,128,.04)!important;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
}}
div[data-testid="stHorizontalBlock"] > [data-testid="column"]:first-child [data-testid="stVerticalBlockBorderWrapper"] .row-sub{{
  font-size:.65rem;color:#777;line-height:1.35;margin:-2px 0 10px 4px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
}}

.compare-bar{{
  font-size:.78rem;padding:8px 12px;margin-bottom:{G};
  border:1px solid rgba(91,141,239,.25);border-radius:8px;
  background:rgba(91,141,239,.06);
}}
.compare-score{{font-weight:600;color:#3D9970}}
.slot-tag{{font-size:.65rem;padding:1px 5px;border-radius:3px;margin-right:4px}}
.slot-1{{background:rgba(91,141,239,.2);color:#5B8DEF}}
.slot-2{{background:rgba(155,89,182,.2);color:#9B59B6}}

div[data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child [data-testid="stVerticalBlockBorderWrapper"]{{
  padding:18px 24px 24px!important;
}}

.detail-panel{{padding:4px 2px 8px}}
.profile-hero{{
  padding:16px 18px 18px;margin-bottom:{SPACE};
  border-radius:12px;border:1px solid rgba(128,128,128,.16);
  background:rgba(255,255,255,.025);
}}
.profile-name-row{{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:8px}}
.profile-name{{margin:0;font-size:1.25rem;font-weight:700;line-height:1.3}}
.dday-badge{{
  font-size:.72rem;font-weight:700;color:#E8A0A0;
  padding:3px 10px;border-radius:20px;
  background:rgba(200,80,80,.15);border:1px solid rgba(200,80,80,.25);
}}
.profile-contact{{
  font-size:.88rem;color:#7EB0FF;font-family:ui-monospace,monospace;
  letter-spacing:.03em;margin-bottom:12px;
}}
.profile-chips{{display:flex;flex-wrap:wrap;gap:6px}}
.profile-chips .chip{{padding:4px 10px;font-size:.72rem;margin:0}}

.section-card{{
  padding:16px 18px;margin-bottom:{SPACE};border-radius:12px;
  border:1px solid rgba(128,128,128,.14);background:rgba(0,0,0,.12);
}}
.section-card.want{{border-left:3px solid #5B8DEF}}
.section-card.have{{border-left:3px solid #3D9970}}
.section-title{{
  font-size:.72rem;font-weight:700;color:#999;text-transform:uppercase;
  letter-spacing:.06em;margin:0 0 14px;
}}
.meta-grid{{
  display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px 16px;margin-bottom:14px;
}}
.meta-item{{
  padding:10px 12px;border-radius:8px;background:rgba(128,128,128,.06);
  border:1px solid rgba(128,128,128,.08);
}}
.meta-lbl{{display:block;font-size:.62rem;color:#777;margin-bottom:4px;font-weight:600}}
.meta-val{{display:block;font-size:.8rem;color:#ddd;line-height:1.45;word-break:keep-all}}
.text-block{{padding-top:4px;border-top:1px solid rgba(128,128,128,.1)}}
.text-block .meta-lbl{{margin-top:10px}}
.text-body{{font-size:.82rem;color:#bbb;line-height:1.65;margin:6px 0 0;word-break:keep-all}}

.detail-hdr-row{{margin-bottom:14px}}
.detail-acts div[data-testid="stButton"] > button{{
  min-height:30px!important;padding:4px 12px!important;font-size:.74rem!important;
  min-width:64px!important;
}}

.rec-section{{margin-top:8px}}
.rec-section-title{{
  font-size:.78rem;font-weight:700;color:#999;margin:0 0 14px;
  padding-bottom:8px;border-bottom:1px solid rgba(128,128,128,.12);
}}
.rec-card{{
  padding:16px 18px;margin-bottom:14px;border-radius:12px;
  border:1px solid rgba(128,128,128,.14);background:rgba(255,255,255,.02);
}}
.rec-card.mutual{{border-color:rgba(61,153,112,.35);background:rgba(61,153,112,.04)}}
.rec-top{{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:12px}}
.rec-name{{font-weight:700;font-size:.95rem;color:#eee}}
.rec-score{{
  font-size:.74rem;color:#5B8DEF;font-weight:600;white-space:nowrap;
  padding:4px 10px;border-radius:20px;background:rgba(91,141,239,.12);
}}
.rec-score.mutual{{color:#5DDBA4;background:rgba(61,153,112,.15)}}
.rec-kw{{margin:12px 0}}
.rec-foot{{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:14px;padding-top:12px;border-top:1px solid rgba(128,128,128,.1)}}
.rec-foot .kw-tip{{margin:0;font-size:.65rem;color:#666}}
.rec-foot div[data-testid="stButton"] > button{{
  min-height:32px!important;padding:5px 18px!important;font-size:.78rem!important;
}}
.kw-row{{gap:7px!important;margin:0}}
.kw-yes{{padding:4px 10px;font-size:.72rem;border-radius:6px}}
.kw-no{{padding:4px 10px;font-size:.72rem;border-radius:6px}}
.kw-filter-row{{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}}
.kw-filter-row div[data-testid="stButton"] > button{{
  min-height:26px!important;padding:2px 10px!important;font-size:.65rem!important;
  border-color:rgba(61,153,112,.35)!important;color:#5DDBA4!important;
}}

.value-badge{{
  font-size:.78rem;font-weight:700;padding:5px 12px;border-radius:20px;white-space:nowrap;
}}
.value-high{{background:rgba(61,153,112,.2);color:#5DDBA4;border:1px solid rgba(61,153,112,.4)}}
.value-mid{{background:rgba(232,168,56,.15);color:#E8C868;border:1px solid rgba(232,168,56,.35)}}
.value-caution{{background:rgba(200,120,80,.12);color:#E8A878;border:1px solid rgba(200,120,80,.3)}}
.value-low{{background:rgba(200,80,80,.15);color:#E89090;border:1px solid rgba(200,80,80,.35)}}

.story-block{{
  margin:14px 0 0;padding:14px 16px;border-radius:10px;line-height:1.65;
  border:1px solid rgba(128,128,128,.14);background:rgba(0,0,0,.12);
}}
.story-block.value-high{{border-left:3px solid #3D9970}}
.story-block.value-mid{{border-left:3px solid #E8C868}}
.story-block.value-caution{{border-left:3px solid #E8A878}}
.story-block.value-low{{border-left:3px solid #C85050}}
.story-head{{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin-bottom:8px}}
.story-rank{{
  font-size:.68rem;font-weight:700;color:#5B8DEF;padding:2px 8px;border-radius:4px;
  background:rgba(91,141,239,.12);
}}
.story-tier{{font-size:.68rem;font-weight:700;color:#999}}
.story-title{{font-size:.78rem;font-weight:700;color:#ddd}}
.story-body{{font-size:.8rem;color:#aaa;margin:0 0 10px;line-height:1.65}}
.value-breakdown{{display:flex;flex-wrap:wrap;gap:8px;margin-top:4px}}
.bd-item{{
  font-size:.65rem;color:#888;padding:3px 8px;border-radius:4px;
  background:rgba(128,128,128,.08);border:1px solid rgba(128,128,128,.1);
}}
.bd-item b{{color:#aaa;margin-right:4px}}
.rec-top .value-badge{{flex-shrink:0}}
.compare-value{{
  display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-top:8px;
}}

.chips{{font-size:.72rem;line-height:1.6;margin-bottom:{G}}}
.chip{{display:inline-block;padding:1px 6px;border-radius:3px;margin-right:3px;background:rgba(128,128,128,.12)}}
.chip-r{{color:#C85050;background:rgba(200,80,80,.12)}}
.chip-g{{color:#3D9970;background:rgba(61,153,112,.12)}}
.chip-w{{color:#E8A838;background:rgba(232,168,56,.14)}}

.box{{
  font-size:.78rem;line-height:1.55;border:1px solid rgba(128,128,128,.15);
  border-radius:8px;padding:10px 12px;margin-bottom:{G};
  word-break:keep-all;overflow-wrap:break-word;
}}
.box-want{{border-left:3px solid #5B8DEF}}
.box-lbl{{font-size:.68rem;color:#888;font-weight:600;margin-bottom:4px}}
.box p{{margin:0 0 4px}}

.mob-back{{display:none}}
.empty-hint{{font-size:.78rem;color:#777;padding:12px 4px;line-height:1.6}}

.kw-tip{{font-size:.68rem;color:#777;margin:2px 0 6px}}
.filter-bar{{
  display:flex;align-items:center;gap:8px;flex-wrap:wrap;
  font-size:.74rem;padding:6px 10px;margin-bottom:{G};
  border-radius:6px;background:rgba(91,141,239,.08);border:1px solid rgba(91,141,239,.2);
}}
.active-filters{{
  display:flex;align-items:center;flex-wrap:wrap;gap:6px;margin-bottom:10px;
  padding:6px 10px;border-radius:6px;background:rgba(128,128,128,.06);
  border:1px solid rgba(128,128,128,.12);
}}
.flt-chip{{
  font-size:.68rem;padding:2px 8px;border-radius:4px;
  background:rgba(91,141,239,.14);border:1px solid rgba(91,141,239,.28);color:#aac4ff;
}}
.flt-chip-kw{{background:rgba(61,153,112,.14);border-color:rgba(61,153,112,.35);color:#5DDBA4}}
[data-testid="stExpander"] summary{{font-size:.82rem!important}}
div[data-testid="stMultiSelect"] [data-baseweb="tag"]{{font-size:.72rem!important}}

/* ── 완료 목록 ── */
.done-toolbar{{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;gap:8px;flex-wrap:wrap}}
.done-count{{font-size:.78rem;color:#888}}
.done-count b{{color:#3D9970;font-weight:600}}
.done-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(420px,1fr));gap:14px}}
.done-card{{
  border:1px solid rgba(61,153,112,.28);border-radius:10px;
  background:rgba(61,153,112,.04);padding:12px 14px;
}}
.done-head{{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:10px;flex-wrap:wrap}}
.done-names{{font-size:.92rem;font-weight:700}}
.done-names .link-icon{{color:#3D9970;margin:0 6px;font-weight:400}}
.done-score{{font-size:.72rem;color:#3D9970;font-weight:600;white-space:nowrap}}
.done-body{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
.done-person{{
  border:1px solid rgba(128,128,128,.14);border-radius:8px;
  padding:8px 10px;background:rgba(0,0,0,.15);min-width:0;
}}
.done-person.missing{{opacity:.55;border-style:dashed}}
.done-pname{{font-size:.82rem;font-weight:600;margin-bottom:4px}}
.done-pmeta{{font-size:.68rem;color:#888;line-height:1.45;margin-bottom:4px}}
.done-contact{{
  font-size:.76rem;color:#5B8DEF;font-family:ui-monospace,monospace;
  margin:4px 0 6px;letter-spacing:.02em;
}}
.done-lbl{{font-size:.62rem;color:#666;font-weight:600;margin:4px 0 2px}}
.done-txt{{font-size:.7rem;color:#aaa;line-height:1.45;
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;
}}
.done-kws{{margin-top:8px;padding-top:8px;border-top:1px solid rgba(128,128,128,.12)}}
.done-empty{{font-size:.82rem;color:#777;padding:24px 8px;text-align:center}}

@media (max-width:768px){{
  section.main > div.block-container{{
    padding:calc(3.5rem + env(safe-area-inset-top,0)) 1rem 1.25rem!important;
  }}
  div[data-testid="stHorizontalBlock"] > [data-testid="column"]:first-child,
  div[data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child{{
    flex:1 1 100%!important;max-width:100%!important;min-width:100%!important;
  }}
  div[data-testid="stHorizontalBlock"] > [data-testid="column"]:first-child div[data-testid="stButton"] > button{{
    min-height:36px!important;
  }}
  .done-grid{{grid-template-columns:1fr}}
  .done-body{{grid-template-columns:1fr}}
  .meta-grid{{grid-template-columns:1fr}}
  .rec-top{{flex-direction:column;gap:8px}}
  .profile-hero{{padding:14px}}
  .section-card{{padding:14px}}
  .mob-back{{display:block;margin-bottom:{G}}}
  div[data-testid="stButton"] > button{{min-height:36px!important}}
  [data-testid="stTextInput"] input{{font-size:16px!important;min-height:40px!important}}
}}
</style>
""",
    unsafe_allow_html=True,
)

for k, v in [("df", None), ("selected", []), ("demo_mode", True), ("load_ver", 0), ("flash", ""), ("chip_filter", None)]:
    if k not in st.session_state:
        st.session_state[k] = v
# 이전 버전 호환
if st.session_state.get("selected_idx") is not None and not st.session_state["selected"]:
    st.session_state["selected"] = [st.session_state.pop("selected_idx")]

with st.sidebar:
    _logo = logo_data_uri()
    st.markdown(
        f'<div class="sidebar-brand">'
        f'<img src="{_logo}" alt="단골팅"/>'
        f'<span>단골팅</span></div>',
        unsafe_allow_html=True,
    )
    st.caption("설정")
    demo_mode = st.toggle("데모 데이터", value=st.session_state["demo_mode"])
    st.session_state["demo_mode"] = demo_mode
    if not demo_mode:
        sheet_url = st.text_input("시트 주소", value=DEFAULT_SHEET_URL, label_visibility="collapsed")
        ws_name = st.text_input("시트 탭", value=DEFAULT_WORKSHEET, label_visibility="collapsed")
    else:
        sheet_url, ws_name = "", ""
    if st.button("새로고침", use_container_width=True):
        st.session_state["load_ver"] += 1
        st.session_state["df"] = None
        st.session_state["selected"] = []
        st.rerun()


@st.cache_data(ttl=60)
def _load(url: str, ws: str, _ver: int) -> pd.DataFrame:
    return load_data(url, ws)


def get_df() -> pd.DataFrame:
    if st.session_state["df"] is not None:
        return st.session_state["df"]
    if demo_mode:
        df = load_demo_data()
    elif sheet_url:
        try:
            df = _load(sheet_url, ws_name, st.session_state["load_ver"])
        except Exception as e:
            st.error(str(e))
            return pd.DataFrame()
    else:
        return pd.DataFrame()
    st.session_state["df"] = df
    return df


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
            if st.button("필터 초기화", key="flt_clr", use_container_width=True):
                clear_all_filters()
                st.rerun()


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
    c1, c2 = st.columns([8, 1])
    with c1:
        st.markdown(f'<div class="active-filters">{parts}</div>', unsafe_allow_html=True)
    with c2:
        if st.button("해제", key="flt_bar_clr", use_container_width=True):
            clear_all_filters()
            st.rerun()


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
        })
    pairs.sort(key=lambda p: p["ts"], reverse=True)
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
    return (
        f'<div class="done-card">'
        f'<div class="done-head">'
        f'<span class="done-names">{html_lib.escape(pair["name_a"])}'
        f'<span class="link-icon">↔</span>{html_lib.escape(pair["name_b"])}</span>'
        f'<span class="done-score">{badge}</span>'
        f'</div>{story}'
        f'<div class="done-body">'
        f'{person_done_html(pair["row_a"])}'
        f'{person_done_html(pair["row_b"], pair["name_b"])}'
        f'</div>{kw_block}</div>'
    )


def do_match(a: int, b: int) -> None:
    df = st.session_state["df"]
    na, nb = df.loc[a, "name"], df.loc[b, "name"]
    if not demo_mode:
        set_matched(sheet_url, a, nb, ws_name)
        set_matched(sheet_url, b, na, ws_name)
    df.loc[a, "matched"], df.loc[a, "matched_w"] = "TRUE", nb
    df.loc[b, "matched"], df.loc[b, "matched_w"] = "TRUE", na
    st.session_state["df"] = df
    st.session_state["flash"] = f"{na} ↔ {nb} 매칭 완료"
    st.session_state["selected"] = []


def toggle_select(idx: int) -> None:
    sel: list = st.session_state["selected"]
    if idx in sel:
        sel.remove(idx)
    elif len(sel) < 2:
        sel.append(idx)
    else:
        sel[1] = idx  # 2명 선택 중이면 두 번째 슬롯 교체
    st.session_state["selected"] = sel


def search_df(frame: pd.DataFrame, query: str) -> pd.DataFrame:
    q = query.strip().lower()
    if not q:
        return frame
    cols = ["name", "job", "region", "have", "want", "w_job", "values", "gender", "depth"]
    mask = pd.Series(False, index=frame.index)
    for col in cols:
        if col in frame.columns:
            mask |= frame[col].astype(str).str.lower().str.contains(q, na=False, regex=False)
    return frame[mask]


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


def render_list_row(idx: int, row, selected: list) -> None:
    """컴팩트 목록 행 — 이름만 버튼, 메타는 한 줄."""
    nm = str(row.get("name", ""))
    prefix = ""
    if idx in selected:
        prefix = "① " if selected.index(idx) == 0 else "② "
    if is_matched(row):
        nm = f"{nm} ✓"
    elif is_closed(row):
        nm = f"{nm} ·종료"
    elif is_rejected(row):
        nm = f"{nm} ·거절"
    sub = (
        f'{chip(row)} '
        f'<span class="chip chip-r">{row.get("dday", "")}</span> '
        f'{row.get("region", "")} · {sjob(row.get("job", ""))}'
    )
    if st.button(f"{prefix}{nm}", key=f"p{idx}", use_container_width=True):
        toggle_select(idx)
        st.rerun()
    st.markdown(f'<div class="row-sub">{sub}</div>', unsafe_allow_html=True)


def render_match_keywords(kws: list[MatchKeyword], prefix: str, clickable: bool = True) -> None:
    """일치 항목 키워드 — 컴팩트 필터 pill."""
    st.markdown(f'<div class="rec-kw">{keywords_html(kws)}</div>', unsafe_allow_html=True)
    if not clickable:
        return
    matched = [k for k in kws if k.matched and k.keyword not in ("—", "")]
    if not matched:
        return
    st.markdown('<div class="kw-filter-row">', unsafe_allow_html=True)
    cols = st.columns(min(len(matched), 4))
    for i, kw in enumerate(matched[:4]):
        with cols[i % len(cols)]:
            if st.button(kw.label, key=f"kw{prefix}{kw.key}{i}"):
                st.session_state["chip_filter"] = {
                    "field": kw.filter_field,
                    "value": kw.filter_value,
                    "label": f"{kw.label}: {kw.keyword}",
                }
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def _meta_item(label: str, value: str) -> str:
    v = html_lib.escape(str(value or "—"))
    return (
        f'<div class="meta-item"><span class="meta-lbl">{html_lib.escape(label)}</span>'
        f'<span class="meta-val">{v}</span></div>'
    )


def profile_hero_html(row) -> str:
    dday = html_lib.escape(str(row.get("dday", "")))
    contact = html_lib.escape(fmt_contact(row.get("contact", "")))
    chips = (
        f'<div class="profile-chips">{chip(row)}'
        f'<span class="chip">{html_lib.escape(str(row.get("gender", "")))}</span>'
        f'<span class="chip">{html_lib.escape(str(row.get("region", "")))}</span>'
        f'<span class="chip">{html_lib.escape(sjob(row.get("job", "")))}</span>'
        f'<span class="chip">{html_lib.escape(syears(row.get("years", "")))}</span>'
        f"</div>"
    )
    return (
        f'<div class="profile-hero">'
        f'<div class="profile-name-row">'
        f'<h2 class="profile-name">{html_lib.escape(str(row.get("name", "")))}</h2>'
        f'<span class="dday-badge">{dday}</span></div>'
        f'<div class="profile-contact">{contact}</div>{chips}</div>'
    )


def profile_sections_html(row) -> str:
    want_txt = html_lib.escape(str(row.get("want", "—")))
    have_txt = html_lib.escape(str(row.get("have", "—")))
    return (
        f'<div class="section-card want">'
        f'<div class="section-title">원하는 조건</div>'
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
        f'<div class="section-title">제공 가치</div>'
        f'<p class="text-body">{have_txt}</p></div>'
    )


def render_person(idx: int, slot: int, show_recommend: bool = True) -> None:
    row = df.loc[idx]
    tag = "①" if slot == 1 else "②"

    st.markdown('<div class="detail-panel">', unsafe_allow_html=True)

    act_l, act_sp, act_r = st.columns([6, 3, 1])
    with act_l:
        st.markdown(
            f'<p class="detail-hdr" style="margin:0;font-size:.78rem;color:#888">'
            f'<span class="slot-tag slot-{slot}">{tag}</span> 프로필</p>',
            unsafe_allow_html=True,
        )
    with act_r:
        btn1, btn2 = st.columns(2)
        with btn1:
            if not is_matched(row) and not is_closed(row):
                if st.button("거절", key=f"r{idx}s{slot}"):
                    do_reject(idx)
                    st.rerun()
        with btn2:
            if st.button("닫기", key=f"x{idx}s{slot}"):
                sel = [i for i in st.session_state["selected"] if i != idx]
                st.session_state["selected"] = sel
                st.rerun()

    st.markdown(profile_hero_html(row), unsafe_allow_html=True)

    if is_matched(row):
        st.success(f"매칭 완료 — {row.get('matched_w', '')}")
    elif is_closed(row):
        st.error("매칭 종료 (거절 2회)")

    st.markdown(profile_sections_html(row), unsafe_allow_html=True)

    if show_recommend and not is_matched(row) and not is_closed(row):
        st.markdown('<div class="rec-section"><div class="rec-section-title">추천 상대</div>', unsafe_allow_html=True)
        for rank, cand in enumerate(recommend(idx, df, 3), 1):
            cr = df.loc[cand.idx]
            cn = html_lib.escape(str(cr.get("name", "")))
            vm = cand.value
            card_cls = "rec-card mutual" if cand.mutual else "rec-card"
            badge = value_badge_html(vm) if vm else ""
            st.markdown(
                f'<div class="{card_cls}">'
                f'<div class="rec-top">'
                f'<span class="rec-name">{cn}</span>'
                f'<span>{badge}</span>'
                f"</div>",
                unsafe_allow_html=True,
            )
            if vm:
                st.markdown(story_block_html(vm, rank), unsafe_allow_html=True)
            render_match_keywords(cand.keywords, f"r{idx}{cand.idx}", clickable=True)
            ft_l, ft_r = st.columns([4, 1])
            with ft_l:
                st.markdown('<span class="kw-tip">키워드 클릭 → 목록 필터</span>', unsafe_allow_html=True)
            with ft_r:
                if st.button("매칭 확정", key=f"m{idx}{cand.idx}s{slot}", type="primary"):
                    do_match(idx, cand.idx)
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def do_reject(i: int) -> None:
    df = st.session_state["df"]
    cur = parse_reject(df.loc[i, "reject"])
    df.loc[i, "reject"] = increment_reject(sheet_url, i, cur, ws_name) if not demo_mode else cur + 1
    st.session_state["df"] = df


df = get_df()
if df.empty:
    st.info("데이터가 없습니다.")
    st.stop()

n = len(df)
m = int(df["matched"].astype(str).str.upper().eq("TRUE").sum())
c = int(df["reject"].apply(parse_reject).ge(2).sum())
r = int((~df["matched"].astype(str).str.upper().eq("TRUE") & df["reject"].apply(parse_reject).eq(1)).sum())
w = int((~df["matched"].astype(str).str.upper().eq("TRUE") & df["reject"].apply(parse_reject).eq(0)).sum())

_logo = logo_data_uri()
st.markdown(
    f'<div class="topbar">'
    f'<div class="topbar-brand">'
    f'<img class="logo-mark" src="{_logo}" alt="단골팅 로고"/>'
    f'<div class="brand-text"><h1>단골팅</h1><div class="brand-sub">매칭 관리</div></div>'
    f'</div>'
    f'<div class="stats">전체 <b>{n}</b> · 대기 <b>{w}</b> · 거절 <b>{r}</b> · 완료 <b>{m}</b> · 종료 <b>{c}</b></div>'
    f'</div>',
    unsafe_allow_html=True,
)
if st.session_state.get("flash"):
    st.success(st.session_state["flash"])
    st.session_state["flash"] = ""

tab1, tab2, tab3 = st.tabs(["매칭 작업", "완료 목록", "원본 데이터"])

with tab1:
    q = st.text_input(
        "검색",
        placeholder="이름 · 직군 · 지역 · 제공가치 · 원하는 것 검색",
        label_visibility="collapsed",
        key="sq",
    )

    render_field_filter_panel(df)
    field_sel = collect_filter_selections()
    cf = st.session_state.get("chip_filter")
    render_active_filter_bar(field_sel, cf)

    left, right = st.columns([22, 78], gap="large")
    selected: list = [i for i in st.session_state.get("selected", []) if i in df.index]

    with left:
        with st.container(border=True):
            fs = st.radio(
                "상태",
                ["전체", "대기", "거절", "완료", "종료"],
                horizontal=True,
                label_visibility="collapsed",
                key="fs",
            )
            sort_by = st.selectbox(
                "정렬",
                ["D-day 임박순", "D-day 여유순", "이름순", "신청순"],
                index=0,
                label_visibility="collapsed",
                key="list_sort",
            )

            fdf = filter_by_status(df.copy(), fs) if fs != "전체" else df.copy()
            fdf = apply_field_filters(fdf, field_sel)
            fdf = apply_keyword_filter(fdf, cf)
            fdf = search_df(fdf, q)
            if sort_by != "신청순":
                fdf = sort_list_df(fdf, sort_by)

            sel_hint = f" · 선택 {len(selected)}/2" if selected else ""
            st.markdown(f'<div class="list-hdr">{len(fdf)}명{sel_hint}</div>', unsafe_allow_html=True)

            for idx, row in fdf.iterrows():
                render_list_row(idx, row, selected)

            if selected:
                if st.button("선택 초기화", key="clr_all", use_container_width=True):
                    st.session_state["selected"] = []
                    st.rerun()

    with right:
        with st.container(border=True):
            st.markdown('<div class="mob-back">', unsafe_allow_html=True)
            if st.button("← 목록", key="mob_back", use_container_width=True):
                st.session_state["selected"] = []
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

            if not selected:
                st.markdown(
                    '<p class="empty-hint">목록에서 1~2명을 선택하세요.<br>'
                    '2명 선택 시 나란히 비교하고 서로 적합도를 확인할 수 있습니다.</p>',
                    unsafe_allow_html=True,
                )
            elif len(selected) == 1:
                render_person(selected[0], 1, show_recommend=True)
                st.caption("한 명 더 선택하면 2명 비교 화면이 열립니다.")
            else:
                a, b = selected[0], selected[1]
                ra, rb = df.loc[a], df.loc[b]
                pair = evaluate(ra, rb)
                vm = pair.value
                kws_ab = analyze_pair(ra, rb)
                kws_ba = analyze_pair(rb, ra)
                badge = value_badge_html(vm) if vm else ""
                st.markdown(
                    f'<div class="compare-bar">'
                    f'<b>{ra["name"]}</b> ↔ <b>{rb["name"]}</b> '
                    f'<div class="compare-value">{badge}'
                    f'<span class="compare-score">{score_label(pair.score, pair.mutual)}</span>'
                    f"</div></div>",
                    unsafe_allow_html=True,
                )
                if vm:
                    st.markdown(story_block_html(vm), unsafe_allow_html=True)
                st.markdown('<div class="box-lbl">① 기준 일치</div>', unsafe_allow_html=True)
                render_match_keywords(kws_ab, f"cmp{a}{b}", clickable=True)
                st.markdown('<div class="box-lbl">② 기준 일치</div>', unsafe_allow_html=True)
                render_match_keywords(kws_ba, f"cmp{b}{a}", clickable=True)
                can_match = (
                    not is_matched(ra) and not is_closed(ra)
                    and not is_matched(rb) and not is_closed(rb)
                )
                if can_match and st.button(f"{ra['name']} ↔ {rb['name']} 매칭 확정", type="primary", use_container_width=True):
                    do_match(a, b)
                    st.rerun()

                col_a, col_b = st.columns(2, gap="medium")
                with col_a:
                    render_person(a, 1, show_recommend=False)
                with col_b:
                    render_person(b, 2, show_recommend=False)

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
