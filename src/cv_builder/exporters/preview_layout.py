"""Paginate a CV story into positioned text lines for the on-screen preview.

Coordinates are page points with the origin in the *top left* corner, which is
what a Tk canvas expects. Line breaking uses the same font metrics as the PDF
exporter, so the preview wraps text where the exported document wraps it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from reportlab.pdfbase import pdfmetrics

from cv_builder.domain import themes
from cv_builder.exporters import page_style
from cv_builder.exporters.story import Gap, Group, Item, Para, main_story, sidebar_story
from cv_builder.exporters.pdf import register_fonts


FONT_NAME = "CVRegular"


@dataclass(frozen=True)
class Line:
    """One laid-out line of text, anchored at its top-left corner."""

    x: float
    y: float
    text: str
    size: float
    color: str
    anchor: str = "nw"


@dataclass
class Page:
    sidebar_color: str
    lines: list[Line] = field(default_factory=list)


def _text_width(text: str, size: float) -> float:
    return pdfmetrics.stringWidth(text, FONT_NAME, size)


def _wrap(text: str, size: float, width: float, left: float, first: float) -> list[tuple[float, str]]:
    """Break text into (x offset, line) pairs; ``\\n`` forces a break."""
    result: list[tuple[float, str]] = []
    for raw in text.split("\n"):
        words = raw.split()
        if not words:
            result.append((left, ""))
            continue
        current = ""
        for word in words:
            offset = left + first if not result else left
            available = width - offset
            candidate = f"{current} {word}" if current else word
            if current and _text_width(candidate, size) > available:
                result.append((offset, current))
                current = word
            else:
                current = candidate
        result.append((left + first if not result else left, current))
    return result


class _Flow:
    """Places paragraphs down a column, starting a new page when needed."""

    def __init__(self, sidebar_color: str, top: float, bottom: float, x: float, width: float):
        self.sidebar_color = sidebar_color
        self.top = top
        self.bottom = bottom
        self.x = x
        self.width = width
        self.pages: list[Page] = [Page(sidebar_color)]
        self.y = top

    @property
    def page(self) -> Page:
        return self.pages[-1]

    def _new_page(self) -> None:
        self.pages.append(Page(self.sidebar_color))
        self.y = self.top

    def _place(self, item: Para, *, allow_split: bool) -> None:
        definition = page_style.style(item.style)
        size = definition["size"]
        leading = definition["leading"]
        color = page_style.resolve_color(item.style, self.sidebar_color)
        lines = _wrap(
            item.text,
            size,
            self.width,
            definition["left_indent"],
            definition["first_line_indent"],
        )
        self.y += definition["space_before"]
        index = 0
        while index < len(lines):
            if self.y + leading > self.bottom and self.y > self.top:
                if not allow_split:
                    return
                self._new_page()
            offset, text = lines[index]
            if text:
                self.page.lines.append(
                    Line(self.x + offset, self.y, text, size, color)
                )
            self.y += leading
            index += 1
        self.y += definition["space_after"]

    def _height(self, item: Para) -> float:
        definition = page_style.style(item.style)
        lines = _wrap(
            item.text,
            definition["size"],
            self.width,
            definition["left_indent"],
            definition["first_line_indent"],
        )
        return (
            definition["space_before"]
            + len(lines) * definition["leading"]
            + definition["space_after"]
        )

    def add(self, story: list[Item], *, paginate: bool = True) -> None:
        for item in story:
            if isinstance(item, Gap):
                self.y += item.height
            elif isinstance(item, Group):
                height = sum(self._height(child) for child in item.items)
                if paginate and self.y + height > self.bottom and self.y > self.top:
                    self._new_page()
                for child in item.items:
                    self._place(child, allow_split=paginate)
            else:
                self._place(item, allow_split=paginate)


def build_pages(data: dict[str, Any]) -> list[Page]:
    """Return every page of the CV as positioned lines."""
    register_fonts()
    theme = themes.get_theme(data.get("theme"))
    sidebar_color = theme["color"]

    flow = _Flow(
        sidebar_color,
        page_style.MAIN_TOP,
        page_style.PAGE_HEIGHT - page_style.MAIN_BOTTOM,
        page_style.MAIN_X,
        page_style.MAIN_WIDTH,
    )
    flow.add(main_story(data))
    pages = flow.pages

    sidebar = _Flow(
        sidebar_color,
        page_style.SIDEBAR_TOP,
        page_style.PAGE_HEIGHT - page_style.MAIN_BOTTOM,
        page_style.SIDEBAR_X,
        page_style.SIDEBAR_TEXT_WIDTH,
    )
    sidebar.add(sidebar_story(data.get("profile", {})), paginate=False)
    pages[0].lines.extend(sidebar.pages[0].lines)

    for number, page in enumerate(pages, start=1):
        page.lines.append(
            Line(
                page_style.PAGE_WIDTH - page_style.PAGE_NUMBER_RIGHT,
                page_style.PAGE_HEIGHT - page_style.PAGE_NUMBER_BOTTOM,
                f"Page {number}",
                page_style.PAGE_NUMBER_SIZE,
                page_style.PAGE_NUMBER_COLOR,
                anchor="se",
            )
        )
    return pages
