"""Sidebar colour themes and the contrast rule that picks the text colour.

A theme is a document property: it is stored in the CV JSON and travels with an
exported file. Text colours are never chosen by hand — they follow from the
measured contrast against the plate.
"""
from __future__ import annotations


# Text colours for a light (white) background. `meta` is for dates, durations
# and locations: readable at small sizes (~5:1 on white) where `muted` — kept
# for the large headline location line — would be too faint to print.
TEXT_DARK = {
    "heading": "#0b0b0b",
    "body": "#161616",
    "meta": "#6b6b6b",
    "muted": "#a9a9a9",
}
# Text colours for a dark plate.
TEXT_LIGHT = {
    "heading": "#e8ebed",
    "body": "#ffffff",
    "meta": "#d5dbdf",
    "muted": "#c6ced3",
}

SIDEBAR_THEMES: tuple[dict[str, str], ...] = (
    {"key": "linkedin", "label": "LinkedIn grey", "color": "#29414c"},
    {"key": "olive-deep", "label": "Deep olive", "color": "#3c5223"},
    {"key": "olive-soft", "label": "Soft olive", "color": "#adc178"},
    {"key": "forest", "label": "Forest green", "color": "#1b512d"},
    {"key": "mint", "label": "Mint", "color": "#c2f8cb"},
    {"key": "ink", "label": "Ink black", "color": "#0b1215"},
    {"key": "midnight", "label": "Midnight navy", "color": "#020c1a"},
)
DEFAULT_THEME = SIDEBAR_THEMES[0]["key"]


def get_theme(key: str | None) -> dict[str, str]:
    """Return a known sidebar theme, falling back to the default one."""
    for theme in SIDEBAR_THEMES:
        if theme["key"] == key:
            return theme
    return SIDEBAR_THEMES[0]


def relative_luminance(color: str) -> float:
    """WCAG relative luminance of a #rrggbb colour."""
    value = color.lstrip("#")
    if len(value) != 6:
        raise ValueError(f"Unsupported colour: {color}")
    channels = []
    for offset in (0, 2, 4):
        channel = int(value[offset : offset + 2], 16) / 255
        channels.append(
            channel / 12.92
            if channel <= 0.03928
            else ((channel + 0.055) / 1.055) ** 2.4
        )
    red, green, blue = channels
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(first: str, second: str) -> float:
    lighter, darker = sorted(
        (relative_luminance(first), relative_luminance(second)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


def sidebar_palette(color: str) -> dict[str, str]:
    """Pick light or dark plate text by measuring contrast against the plate."""
    light = contrast_ratio(color, TEXT_LIGHT["body"])
    dark = contrast_ratio(color, TEXT_DARK["body"])
    return TEXT_LIGHT if light >= dark else TEXT_DARK


def sidebar_uses_dark_text(color: str) -> bool:
    return sidebar_palette(color) is TEXT_DARK
