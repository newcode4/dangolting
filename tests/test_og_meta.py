import inspect

from utils import og_meta


def test_og_meta_static_tags():
    src = inspect.getsource(og_meta._meta_pairs)
    assert "og:image" in src
    assert "inject_og_meta" in inspect.getsource(og_meta)


def test_og_image_cache_bust():
    url = og_meta.og_image_url(base="https://example.streamlit.app")
    assert ".png" in url
    assert og_meta.OG_IMAGE_VER in url


def test_og_svg_utf8_korean():
    from pathlib import Path

    text = Path(__file__).resolve().parents[1].joinpath("static", "og.svg").read_text(
        encoding="utf-8"
    )
    assert "단골팅" in text
    png = Path(__file__).resolve().parents[1].joinpath("static", "og.png")
    assert png.is_file()
