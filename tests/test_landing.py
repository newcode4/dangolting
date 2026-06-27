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
