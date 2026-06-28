"""Streamlit Cloud chrome hide + OG PNG."""
import inspect
from pathlib import Path

from utils import og_meta, streamlit_shell


def test_shell_hide_no_body_class_gate():
    css = streamlit_shell.SHELL_HIDE_CSS
    assert "body.dgt-landing" not in css
    assert "appCreatorAvatar" in css
    assert "share.streamlit.io/user" in css
    src = inspect.getsource(streamlit_shell.inject_streamlit_cloud_chrome_hide)
    assert "dgt-shell-hide" in src
    assert "dgtHideChrome" in streamlit_shell._HIDE_JS
    assert "MutationObserver" in src


def test_og_uses_png_github_raw():
    url = og_meta.og_image_url()
    assert ".png" in url
    assert "raw.githubusercontent.com" in url
    assert og_meta.OG_IMAGE_VER in url


def test_og_injects_parent_head():
    src = inspect.getsource(og_meta._meta_pairs)
    assert "og:image" in src
    src2 = inspect.getsource(og_meta.inject_og_meta)
    assert "window.parent.document" in src2


def test_og_png_exists():
    png = Path(__file__).resolve().parents[1] / "static" / "og.png"
    assert png.is_file()
    assert png.stat().st_size > 5000


def test_app_injects_shell_hide_early():
    app_src = Path(__file__).resolve().parents[1].joinpath("app.py").read_text(encoding="utf-8")
    idx_shell = app_src.find("inject_streamlit_cloud_chrome_hide()")
    idx_gate = app_src.find("_public_entry_gate(logo_data_uri())")
    assert idx_shell > 0 and idx_shell < idx_gate
