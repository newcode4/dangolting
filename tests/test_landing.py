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
    assert "initHookBars" in html


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
