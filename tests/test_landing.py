from utils.landing_config import APPLICATION_FORM_URL, CONTENT_MAX_WIDTH


def test_application_form_url():
    assert APPLICATION_FORM_URL == "https://forms.gle/HwxDTsoscugsFhKy7"


def test_content_max_width():
    assert CONTENT_MAX_WIDTH == 100
