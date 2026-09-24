#!/usr/bin/env python3
"""Render the Finder window background for the macOS DMG.

The output is committed (`assets/dmg/background.png`), so CI never renders it
and the build does not depend on the runner's fonts. Re-run this script only
when the design changes; it needs macOS for the SF Pro / New York faces.

Geometry is authored in Finder points and must stay in sync with
`packaging/dmg_settings.py` (window size and icon centres). The PNG is
rendered at 2x and tagged 144 dpi, which Finder shows at point size on both
Retina and non-Retina displays.

Finder draws icon labels in a dark colour on a background picture even in
Dark Mode, so the canvas must stay light.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "assets" / "dmg" / "background.png"

# Finder window content size and icon centres, in points. The canvas runs
# BLEED points past the designed area so no title-bar height leaves a gap.
WIDTH, HEIGHT = 660, 420
BLEED = 40
APP_CENTER = (170, 236)
APPS_CENTER = (490, 236)

RETINA = 2
SUPERSAMPLE = 2
K = RETINA * SUPERSAMPLE

# Calm Workspace tokens (wiki/references/cv-builder-design-spec.md §5.1).
BACKGROUND_TOP = (248, 249, 252)
BACKGROUND_BOTTOM = (237, 241, 249)
TEXT = (23, 32, 51)
MUTED = (102, 112, 133)
BORDER = (215, 221, 232)
ACCENT = (47, 107, 255)

SYSTEM_FONTS = Path("/System/Library/Fonts")


def font(name: str, size: float, variation: str) -> ImageFont.FreeTypeFont:
    face = ImageFont.truetype(str(SYSTEM_FONTS / name), round(size * K))
    face.set_variation_by_name(variation)
    return face


def px(value: float) -> int:
    return round(value * K)


def vertical_gradient(size: tuple[int, int]) -> Image.Image:
    column = Image.new("RGB", (1, size[1]))
    for y in range(size[1]):
        t = y / (size[1] - 1)
        column.putpixel(
            (0, y),
            tuple(round(a + (b - a) * t) for a, b in zip(BACKGROUND_TOP, BACKGROUND_BOTTOM)),
        )
    return column.resize(size)


def glow(canvas: Image.Image, center: tuple[float, float], radius: float, color, alpha: int) -> None:
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    cx, cy = center
    ImageDraw.Draw(layer).ellipse(
        [px(cx - radius), px(cy - radius), px(cx + radius), px(cy + radius)],
        fill=(*color, alpha),
    )
    canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(px(radius * 0.55))))


def slot(canvas: Image.Image, center: tuple[float, float]) -> None:
    """Soft card the icon and its Finder label sit on."""
    cx, cy = center
    box = [px(cx - 92), px(cy - 84), px(cx + 92), px(cy + 110)]
    radius = px(26)

    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shifted = [box[0], box[1] + px(6), box[2], box[3] + px(6)]
    ImageDraw.Draw(shadow).rounded_rectangle(shifted, radius, fill=(23, 32, 51, 22))
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(px(12))))

    card = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle(
        box, radius, fill=(255, 255, 255, 200), outline=(*BORDER, 255), width=px(1)
    )
    canvas.alpha_composite(card)


def rounded_line(draw: ImageDraw.ImageDraw, start, end, width: float, color) -> None:
    draw.line([start, end], fill=color, width=px(width))
    r = px(width) / 2
    for x, y in (start, end):
        draw.ellipse([x - r, y - r, x + r, y + r], fill=color)


def drag_arrow(canvas: Image.Image) -> None:
    draw = ImageDraw.Draw(canvas)
    y = APP_CENTER[1]
    left, right = APP_CENTER[0] + 108, APPS_CENTER[0] - 108
    dash, gap, stroke = 7, 6, 2.5

    x = left
    while x + dash <= right - 10:
        rounded_line(draw, (px(x), px(y)), (px(x + dash), px(y)), stroke, ACCENT)
        x += dash + gap

    tip = (px(right), px(y))
    for dy in (-8, 8):
        rounded_line(draw, (px(right - 8), px(y + dy)), tip, stroke, ACCENT)

    caption = font("SFNS.ttf", 11, "Medium")
    draw.text(
        (px((left + right) / 2), px(y - 16)),
        "Drag to install",
        font=caption,
        fill=MUTED,
        anchor="ms",
    )


def tracked_text(draw, center_x: float, baseline: float, text: str, face, tracking: float, color) -> None:
    widths = [face.getlength(ch) for ch in text]
    total = sum(widths) + px(tracking) * (len(text) - 1)
    x = px(center_x) - total / 2
    for ch, w in zip(text, widths):
        draw.text((x, px(baseline)), ch, font=face, fill=color, anchor="ls")
        x += w + px(tracking)


def headline(canvas: Image.Image) -> None:
    draw = ImageDraw.Draw(canvas)
    tracked_text(
        draw, WIDTH / 2, 46, "CV BUILDER", font("SFNS.ttf", 10.5, "Semibold"), 2.2, ACCENT
    )

    regular = font("NewYork.ttf", 26, "Medium")
    italic = font("NewYorkItalic.ttf", 26, "Medium Italic")
    runs = [
        ("You’ll definitely find your ", regular, TEXT),
        ("dream offer", italic, ACCENT),
        (".", regular, TEXT),
    ]
    total = sum(face.getlength(text) for text, face, _ in runs)
    x = px(WIDTH / 2) - total / 2
    for text, face, color in runs:
        draw.text((x, px(84)), text, font=face, fill=color, anchor="ls")
        x += face.getlength(text)


def footer(canvas: Image.Image) -> None:
    draw = ImageDraw.Draw(canvas)
    draw.text(
        (px(WIDTH / 2), px(HEIGHT - 26)),
        "Works offline  ·  Your CVs never leave your Mac",
        font=font("SFNS.ttf", 11, "Regular"),
        fill=MUTED,
        anchor="ms",
    )


def render() -> Image.Image:
    canvas = vertical_gradient((px(WIDTH), px(HEIGHT + BLEED))).convert("RGBA")
    glow(canvas, (WIDTH - 40, -30), 230, ACCENT, 34)
    glow(canvas, (40, HEIGHT + 40), 210, (143, 179, 255), 46)
    slot(canvas, APP_CENTER)
    slot(canvas, APPS_CENTER)
    drag_arrow(canvas)
    headline(canvas)
    footer(canvas)
    size = (WIDTH * RETINA, (HEIGHT + BLEED) * RETINA)
    return canvas.convert("RGB").resize(size, Image.Resampling.LANCZOS)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    render().save(args.output, dpi=(72 * RETINA, 72 * RETINA), optimize=True)
    print(f"Created: {args.output}")


if __name__ == "__main__":
    main()
