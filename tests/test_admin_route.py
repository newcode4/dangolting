from utils.admin_route import (
    DEFAULT_ADMIN_PATH,
    admin_entry_path,
    landing_preview_path,
)


def test_admin_entry_path_default():
    assert admin_entry_path(slug="dgt-manage") == "/?p=dgt-manage"


def test_landing_preview_path():
    assert landing_preview_path() == "/?view=landing"


def test_default_admin_path():
    assert DEFAULT_ADMIN_PATH == "dgt-manage"
    assert admin_entry_path(slug=DEFAULT_ADMIN_PATH) == f"/?p={DEFAULT_ADMIN_PATH}"
