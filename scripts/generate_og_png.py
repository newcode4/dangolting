"""static/og.png 생성 — Kakao OG는 PNG/JPG만 안정 지원."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "static" / "og.png"
W, H = 1200, 630

FONT_CANDIDATES = (
    Path(r"C:\Windows\Fonts\malgunbd.ttf"),
    Path(r"C:\Windows\Fonts\malgun.ttf"),
    Path("/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"),
    Path("/System/Library/Fonts/AppleSDGothicNeo.ttc"),
)


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in FONT_CANDIDATES:
        if path.is_file():
            try:
                return ImageFont.truetype(str(path), size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def main() -> None:
    img = Image.new("RGB", (W, H), "#080b12")
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, W, 180), fill="#0f172a")
    draw.ellipse((320, -120, 880, 280), fill="#1d4ed8")

    title = _font(52, bold=True)
    sub = _font(22)
    small = _font(16)

    draw.text((80, 72), "단골팅", font=_font(28, bold=True), fill="#f1f5f9")
    draw.text((80, 160), "서로에게 진짜 도움이 되는", font=title, fill="#93c5fd")
    draw.text((80, 230), "비즈니스 파트너,", font=title, fill="#f1f5f9")
    draw.text((80, 300), "한 명이면 충분합니다", font=title, fill="#f1f5f9")
    draw.text((80, 390), "운영진이 직접 찾아드립니다 · 5만 원 · 소개 없으면 전액 환불", font=sub, fill="#94a3b8")
    draw.rounded_rectangle((80, 450, 360, 510), radius=28, fill="#2563eb")
    draw.text((120, 468), "지금 내 파트너 찾기 →", font=small, fill="#ffffff")
    draw.text((80, 560), "dangolting.streamlit.app", font=small, fill="#475569")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, format="PNG", optimize=True)
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
