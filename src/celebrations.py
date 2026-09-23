"""Generate shareable weekly achievement cards locally with Pillow."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def _center(draw: ImageDraw.ImageDraw, text: str, y: int, font: ImageFont.ImageFont, fill: str) -> None:
    box = draw.textbbox((0, 0), text, font=font)
    draw.text(((1080 - (box[2] - box[0])) / 2, y), text, font=font, fill=fill)


def generate_achievement_card(weekly_score: float) -> bytes:
    """Return a phone-friendly 1080×1350 PNG achievement card."""
    width, height = 1080, 1350
    image = Image.new("RGB", (width, height), "#0B0614")
    draw = ImageDraw.Draw(image)
    for y in range(height):
        blend = y / height
        color = (
            int(11 + 22 * blend),
            int(6 + 10 * blend),
            int(20 + 34 * blend),
        )
        draw.line((0, y, width, y), fill=color)

    draw.rounded_rectangle((70, 70, 1010, 1280), radius=58, fill="#171024", outline="#8B5CF6", width=3)
    draw.ellipse((395, 260, 685, 550), fill="#201536", outline="#A78BFA", width=5)
    for x, y, r in ((160, 190, 9), (890, 230, 7), (180, 1070, 6), (905, 1040, 10), (820, 150, 4)):
        draw.ellipse((x-r, y-r, x+r, y+r), fill="#A78BFA")

    title = "PERFECT WEEK" if weekly_score >= 100 else "AMAZING WEEK"
    _center(draw, "ERUMAA'S DAILY", 135, _font(34, True), "#B8AEC9")
    _center(draw, title, 590, _font(58, True), "#F5F3FF")
    _center(draw, "ERUMAAA  ♥", 680, _font(42, True), "#A78BFA")
    _center(draw, f"{weekly_score:.0f}%", 335, _font(94, True), "#F5F3FF")
    _center(draw, "THIS WEEK", 780, _font(30, True), "#81758F")
    _center(draw, "I'm proud of you.", 910, _font(42), "#F5F3FF")
    _center(draw, "Keep going, Alagiii. ♥", 980, _font(38), "#B8AEC9")
    _center(draw, "Small habits · Better days", 1165, _font(26), "#81758F")
    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()
