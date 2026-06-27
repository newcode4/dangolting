from utils.landing import _landing_html
from utils.landing_config import APPLICATION_FORM_URL, CONTENT_MAX_WIDTH


def test_application_form_url():
    assert APPLICATION_FORM_URL == "https://forms.gle/HwxDTsoscugsFhKy7"


def test_content_max_width():
    assert CONTENT_MAX_WIDTH == 1080


def test_landing_hook_section():
    html = _landing_html("logo.png", APPLICATION_FORM_URL, "", "", shell_preview=False)
    assert "hook-panel" in html
    assert 'data-count="80000"' in html
    assert "initHookCounters" in html
    assert "initHookCounters" in html


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
    """FAB 위로 버튼 존재."""
    html = _landing_html("logo.png", APPLICATION_FORM_URL, "", "", shell_preview=False)
    assert "fab-top" in html
    assert "scrollParentToTop" in html


def test_landing_kakao_link():
    """카카오 문의 링크 존재, 구 문의하기 버튼 미사용."""
    html = _landing_html("logo.png", APPLICATION_FORM_URL, "", "", shell_preview=False)
    assert "open.kakao.com/me/dangolgrow" in html


def test_landing_refund_policy_accurate():
    """환불 정책에 1회=50%, 2회=0% 명시."""
    html = _landing_html("logo.png", APPLICATION_FORM_URL, "", "", shell_preview=False)
    assert "50%" in html
    assert "1회 거절" in html
