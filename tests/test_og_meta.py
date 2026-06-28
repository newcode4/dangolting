import inspect

from utils import og_meta


def test_og_meta_static_tags():
    src = inspect.getsource(og_meta.inject_og_meta)
    assert 'property="og:image"' in src
    assert "OG_IMAGE_VER" in src
    assert "inject_og_meta" in src


def test_og_image_cache_bust():
    url = og_meta.og_image_url(base="https://example.streamlit.app")
    assert url.startswith("https://example.streamlit.app/app/static/og.svg?v=")


def test_og_svg_utf8_korean():
    from pathlib import Path

    text = Path(__file__).resolve().parents[1].joinpath("static", "og.svg").read_text(
        encoding="utf-8"
    )
    assert "단골팅" in text
    assert "진짜 도움이 되는" in text
    assert "???" not in text
