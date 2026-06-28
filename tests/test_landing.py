from pathlib import Path

from utils.landing import _landing_html
from utils.landing_config import APPLICATION_FORM_URL, CONTENT_MAX_WIDTH


def test_application_form_url():
    assert APPLICATION_FORM_URL == "https://forms.gle/HwxDTsoscugsFhKy7"


def test_content_max_width():
    assert CONTENT_MAX_WIDTH == 1080


def test_landing_hook_section():
    html = _landing_html("logo.png", APPLICATION_FORM_URL, "", "", shell_preview=False)
    assert "hook-panel" in html
    assert 'data-count="10"' in html
    assert 'data-suffix="배+"' in html
    assert "의뢰를 주고받는 파트너" in html
    assert "initHookCounters" in html
    assert "syncHookLayout" in html
    assert "data-hook-layout" in html
    assert "hook-hero-stack" in html
    assert "hook-hero-glow" in html


def test_landing_mobile_line_breaks():
    html = _landing_html("logo.png", APPLICATION_FORM_URL, "", "", shell_preview=False)
    assert "한 번 같이 일해보고<br/>" in html
    assert "모임에 수십 번 나가도 —<br class=\"br-sm\"/>" in html
    assert "고민 없이 일을 맡기고,<br class=\"br-sm\"/>" in html
    css = Path(__file__).resolve().parents[1].joinpath("assets", "landing-page.css").read_text(
        encoding="utf-8"
    )
    assert "br.br-sm" in css

    html = _landing_html("logo.png", APPLICATION_FORM_URL, "/*a*/", "", css_rev="123_456")
    assert 'name="dgt-css-rev" content="123_456"' in html


def test_landing_reads_css_fresh():
    import inspect

    from utils import landing

    src = inspect.getsource(landing.render_landing_page)
    assert "_read_css(_PAGE_CSS_PATH)" in src
    assert "_css_revision()" in src
    assert "dgt-css-rev" in inspect.getsource(landing._landing_html)


def test_landing_hook_css_uses_layout_attribute():
    css = (Path(__file__).resolve().parents[1] / "assets" / "landing-page.css").read_text(encoding="utf-8")
    assert 'html[data-hook-layout="desktop"]' in css
    assert 'html[data-hook-layout="mobile"]' in css
    assert "@media (max-width: 520px)" not in css.split(".hook-climax")[1].split(".hook-cta")[0]


def test_landing_offer_box():
    html = _landing_html("logo.png", APPLICATION_FORM_URL, "", "", shell_preview=False)
    assert 'id="offer"' in html
    assert "offer-box" in html
    assert "offer-list" in html
    assert "offer-price" in html


def test_landing_plain_language():
    """업계 표현(결이 맞는 / 찐) 대신 일반 카피만 노출."""
    html = _landing_html("logo.png", APPLICATION_FORM_URL, "", "", shell_preview=False)
    assert "결이 맞" not in html
    assert "찐" not in html


def test_landing_no_duplicate_stat_grid():
    """hook-panel과 stat-grid 숫자 중복 제거 — stat-grid 미사용."""
    html = _landing_html("logo.png", APPLICATION_FORM_URL, "", "", shell_preview=False)
    assert 'class="stat-grid"' not in html


def test_landing_growth_chart():
    """바 차트 대신 SVG 꺾은선 그래프 사용."""
    html = _landing_html("logo.png", APPLICATION_FORM_URL, "", "", shell_preview=False)
    assert "growth-chart" in html
    assert "chart-path-solo" in html
    assert "chart-path-duo" in html
    assert "initGrowthChart" in html
    assert "hook-bar-fill" not in html


def test_landing_vs_table():
    """VS 테이블 (오프라인 vs 단골팅) 존재."""
    html = _landing_html("logo.png", APPLICATION_FORM_URL, "", "", shell_preview=False)
    assert "vs-table" in html
    assert "vs-col--old" in html
    assert "vs-col--new" in html


def test_landing_hero_fullscreen():
    """히어로 풀스크린 + 스크롤 힌트."""
    html = _landing_html("logo.png", APPLICATION_FORM_URL, "", "", shell_preview=False)
    assert "hero--fullscreen" in html
    assert "hero-scroll-hint" in html
    assert "setHeroHeight" in html


def test_landing_fab():
    """FAB 위로 버튼 — injectFAB 함수로 부모 document에 주입."""
    html = _landing_html("logo.png", APPLICATION_FORM_URL, "", "", shell_preview=False)
    assert "injectFAB" in html
    assert "scrollParentToTop" in html
    assert "dgt-fab-top" in html
    assert "max-width:768px" in html


def test_landing_footer_admin_link():
    """푸터 관리자 진입 링크 — admin_entry_path 쿼리 + postMessage 네비."""
    html = _landing_html(
        "logo.png",
        APPLICATION_FORM_URL,
        "",
        "",
        admin_url="/?p=dangol-admin",
        admin_slug="dangol-admin",
    )
    assert "footer-link-admin" in html
    assert 'href="/?p=dangol-admin"' in html
    assert 'target="_blank"' in html
    assert 'data-admin-go="/?p=dangol-admin"' in html
    assert 'name="dgt-admin-slug" content="dangol-admin"' in html
    assert "dgt-navigate" in html
    assert "dgt-nav-bridge" in html
    assert "관리자" in html


def test_landing_kakao_link():
    """카카오 문의 링크 존재, 구 문의하기 버튼 미사용."""
    html = _landing_html("logo.png", APPLICATION_FORM_URL, "", "", shell_preview=False)
    assert "open.kakao.com/me/dangolgrow" in html


def test_landing_founder_story():
    """창업자 스토리 섹션 존재 + 비즈니스 컨텍스트."""
    html = _landing_html("logo.png", APPLICATION_FORM_URL, "", "", shell_preview=False)
    assert "founder-card" in html
    assert "이주환" in html
    assert "비즈니스 파트너 큐레이터" in html


def test_landing_business_positioning():
    """이해관계 중심 포지셔닝 카피."""
    html = _landing_html("logo.png", APPLICATION_FORM_URL, "", "", shell_preview=False)
    assert "이해관계" in html
    assert "target-grid" in html
    assert "레퍼럴" in html


def test_landing_refund_policy_accurate():
    """환불 정책: 소개0회=전액환불, 1회=50%, 2회=0%."""
    html = _landing_html("logo.png", APPLICATION_FORM_URL, "", "", shell_preview=False)
    assert "50%" in html
    assert "소개 1회" in html
    assert "소개 2회" in html
    assert "소개 0회" in html
    assert "전액 환불" in html
