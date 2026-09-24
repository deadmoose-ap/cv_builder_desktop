"""Page geometry and typography of the rendered CV.

Both renderers (`pdf.py` and `preview_layout.py`) read their constants from
here, so the preview cannot silently drift away from the exported document.
Colour *themes* belong to the document and live in `domain.themes`.
"""
from __future__ import annotations

from typing import Any

from cv_builder.domain.layouts import is_single
from cv_builder.domain.themes import TEXT_DARK, sidebar_palette


PAGE_WIDTH = 612.0
PAGE_HEIGHT = 792.0
SIDEBAR_WIDTH = 176.0
MAIN_X = 197.0
MAIN_WIDTH = 381.0
MAIN_TOP = 40.0
MAIN_BOTTOM = 38.0
SIDEBAR_X = 22.0
SIDEBAR_TOP = 43.0
SIDEBAR_TEXT_WIDTH = 132.0
# Single-column (ATS) layout: symmetric side margins, the same vertical rhythm
# as the main column of the sidebar layout.
SINGLE_X = 48.0
SINGLE_WIDTH = PAGE_WIDTH - 2 * SINGLE_X

# Style name -> size, leading, spacing, colour role and indents.
STYLES: dict[str, dict[str, Any]] = {
    "name": {"size": 28, "leading": 32, "space_after": 7, "color": "heading"},
    "headline": {"size": 12.6, "leading": 15.5, "space_after": 2, "color": "body"},
    "location": {"size": 12, "leading": 15, "space_after": 20, "color": "muted"},
    # Single-column layout only: the contact line and the portfolio links under
    # it, and the skills/languages paragraphs. Contacts use the body colour —
    # they are data a parser and a recruiter must read, not decoration.
    "contact": {"size": 10.5, "leading": 14, "space_after": 2, "color": "body"},
    "portfolio": {"size": 10, "leading": 13, "space_after": 1, "color": "meta"},
    "inline": {"size": 10.5, "leading": 15.1, "space_after": 9, "color": "body"},
    "section": {
        "size": 17,
        "leading": 21,
        "space_before": 11,
        "space_after": 10,
        "color": "heading",
    },
    # The experience header is a four-step ladder: the company is the anchor
    # (bold, largest), the role sits one step below it, and the dates and the
    # location trail off in grey at decreasing size.
    "company": {
        "size": 13,
        "leading": 16,
        "space_after": 2,
        "color": "heading",
        "bold": True,
    },
    "role": {"size": 11.5, "leading": 14.5, "space_after": 1, "color": "body"},
    "dates": {"size": 10, "leading": 13, "space_after": 2, "color": "meta"},
    "place": {"size": 9.5, "leading": 12.5, "space_after": 7, "color": "meta"},
    "body": {"size": 10.5, "leading": 15.1, "space_after": 9, "color": "body"},
    "bullet": {
        "size": 10.5,
        "leading": 14.5,
        "space_after": 3,
        "color": "body",
        "left_indent": 12,
        "first_line_indent": -9,
    },
    "subhead": {
        "size": 10.5,
        "leading": 13,
        "space_before": 4,
        "space_after": 2,
        "color": "body",
        "bold": True,
    },
    "side_head": {
        "size": 11.5,
        "leading": 14,
        "space_after": 5,
        "color": "heading",
        "bold": True,
    },
    "side_body": {"size": 9.5, "leading": 12, "space_after": 4, "color": "body"},
    "side_bullet": {
        "size": 9.5,
        "leading": 12,
        "space_after": 3,
        "color": "body",
        "left_indent": 8,
        "first_line_indent": -6,
    },
}
SIDEBAR_STYLES = ("side_head", "side_body", "side_bullet")


def frame_geometry(layout: str | None) -> tuple[float, float, float, float]:
    """(x, top, bottom, width) of the text column the story flows through."""
    if is_single(layout):
        return SINGLE_X, MAIN_TOP, MAIN_BOTTOM, SINGLE_WIDTH
    return MAIN_X, MAIN_TOP, MAIN_BOTTOM, MAIN_WIDTH


def style(name: str) -> dict[str, Any]:
    """Return a fully populated style definition."""
    defaults = {
        "size": 10.5,
        "leading": 15,
        "space_before": 0.0,
        "space_after": 0.0,
        "color": "body",
        "left_indent": 0.0,
        "first_line_indent": 0.0,
        "bold": False,
    }
    defaults.update(STYLES[name])
    return defaults


def resolve_color(style_name: str, sidebar_color: str) -> str:
    """Resolve a style's colour role against the surface it is drawn on."""
    role = style(style_name)["color"]
    palette = sidebar_palette(sidebar_color) if style_name in SIDEBAR_STYLES else TEXT_DARK
    return palette[role]
