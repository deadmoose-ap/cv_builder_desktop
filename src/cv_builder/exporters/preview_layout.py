"""Paginate a CV story into positioned text lines for the on-screen preview.

Coordinates are page points with the origin in the *top left* corner, which is
what a Tk canvas expects. Line breaking uses the same font metrics as the PDF
exporter, so the preview wraps text where the exported document wraps it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from reportlab.pdfbase import pdfmetrics

from cv_builder.domain import layouts, themes
from cv_builder.domain.locales import is_cjk
from cv_builder.exporters import page_style
from cv_builder.exporters.story import (
    Gap,
    Group,
    Item,
    Para,
    main_story,
    sidebar_story,
    single_column_story,
)
from cv_builder.exporters.pdf import bold_font_for_locale, register_fonts


FONT_NAME = "CVRegular"
# ReportLab breaks lines on whitespace *except* the non-breaking space, while
# `str.split()` breaks on it too. Splitting the same way keeps a skill glued
# with U+00A0 on one line in the preview exactly as in the PDF.
_BREAKABLE_SPACE = re.compile(r"[^\S\u00a0]+")


@dataclass(frozen=True)
class Line:
    """One laid-out line of text, anchored at its top-left corner."""

    x: float
    y: float
    text: str
    size: float
    color: str
    anchor: str = "nw"
    bold: bool = False


@dataclass
class Page:
    sidebar_color: str
    layout: str = layouts.DEFAULT_LAYOUT
    lines: list[Line] = field(default_factory=list)


def _text_width(text: str, size: float, font: str) -> float:
    return pdfmetrics.stringWidth(text, font, size)


def _wrap(
    text: str,
    size: float,
    width: float,
    left: float,
    first: float,
    font: str,
    cjk: bool = False,
) -> list[tuple[float, str]]:
    """Break text into (x offset, line) pairs; ``\\n`` forces a break.

    ``cjk`` mirrors ReportLab's ``wordWrap="CJK"``: scripts written without
    spaces break between characters instead of between words.
    """
    result: list[tuple[float, str]] = []

    def offset() -> float:
        return left + first if not result else left

    def available() -> float:
        return width - offset()

    def append_split_word(word: str) -> None:
        """Place a word that is wider than the available line width."""
        remainder = word
        while remainder:
            fitted = ""
            for character in remainder:
                candidate = fitted + character
                if fitted and _text_width(candidate, size, font) > available():
                    break
                fitted = candidate
            if not fitted:
                # Keep making progress even when a font reports one glyph wider
                # than the available column (ReportLab also places that glyph).
                fitted = remainder[0]
            result.append((offset(), fitted))
            remainder = remainder[len(fitted) :]

    for raw in text.split("\n"):
        units = (
            list(raw.strip())
            if cjk
            else [unit for unit in _BREAKABLE_SPACE.split(raw) if unit]
        )
        if not units:
            result.append((left, ""))
            continue
        current = ""
        for unit in units:
            if cjk:
                candidate = current + unit
                if current and _text_width(candidate, size, font) > available():
                    result.append((offset(), current))
                    current = ""
                    candidate = unit
                # A single CJK glyph should fit in the column; keep the
                # fallback so a pathological font still makes progress.
                if _text_width(candidate, size, font) <= available():
                    current = candidate
                else:
                    result.append((offset(), unit))
                    current = ""
                continue
            candidate = f"{current} {unit}" if current else unit
            if current and _text_width(candidate, size, font) > available():
                # ReportLab uses the remaining line for a word only when the
                # word itself is wider than a full line. Ordinary words move
                # intact to the next line instead of being split here.
                full_line_available = width - left
                if _text_width(unit, size, font) > full_line_available:
                    prefix = ""
                    for character in unit:
                        candidate_with_prefix = f"{current} {prefix}{character}"
                        if (
                            prefix
                            and _text_width(candidate_with_prefix, size, font)
                            > available()
                        ):
                            break
                        prefix += character
                    if prefix:
                        result.append((offset(), f"{current} {prefix}"))
                        append_split_word(unit[len(prefix) :])
                    else:
                        result.append((offset(), current))
                        append_split_word(unit)
                    current = ""
                    continue
                result.append((offset(), current))
                current = ""
                candidate = unit
            if _text_width(candidate, size, font) <= available():
                current = candidate
            else:
                append_split_word(unit)
                current = ""
        if current:
            result.append((offset(), current))
    return result


class _Flow:
    """Places paragraphs down a column, starting a new page when needed."""

    def __init__(
        self,
        sidebar_color: str,
        top: float,
        bottom: float,
        x: float,
        width: float,
        font: str = FONT_NAME,
        bold_font: str | None = None,
        cjk: bool = False,
        layout: str = layouts.DEFAULT_LAYOUT,
    ):
        self.sidebar_color = sidebar_color
        self.layout = layout
        self.font = font
        self.bold_font = bold_font or font
        self.cjk = cjk
        self.top = top
        self.bottom = bottom
        self.x = x
        self.width = width
        self.pages: list[Page] = [Page(sidebar_color, layout)]
        self.y = top
        # ReportLab drops a flowable's space_before at the top of a frame and
        # otherwise overlaps it with the previous flowable's space_after
        # (Frame._add). Mirroring that here is what keeps the preview's page
        # breaks identical to the exported ones.
        self.at_top = True
        self.previous_space_after = 0.0

    @property
    def page(self) -> Page:
        return self.pages[-1]

    def _new_page(self) -> None:
        self.pages.append(Page(self.sidebar_color, self.layout))
        self.y = self.top
        self.at_top = True
        self.previous_space_after = 0.0

    @staticmethod
    def _leading_space(definition: dict, previous_after: float, at_top: bool) -> float:
        if at_top:
            return 0.0
        return max(definition["space_before"] - previous_after, 0.0)

    def _font_for(self, definition: dict) -> str:
        return self.bold_font if definition["bold"] else self.font

    def _place(self, item: Para, *, allow_split: bool) -> None:
        definition = page_style.style(item.style)
        size = definition["size"]
        leading = definition["leading"]
        bold = definition["bold"]
        color = page_style.resolve_color(item.style, self.sidebar_color)
        lines = _wrap(
            item.text,
            size,
            self.width,
            definition["left_indent"],
            definition["first_line_indent"],
            self._font_for(definition),
            self.cjk,
        )
        self.y += self._leading_space(
            definition, self.previous_space_after, self.at_top
        )
        index = 0
        while index < len(lines):
            if self.y + leading > self.bottom and self.y > self.top:
                if not allow_split:
                    return
                self._new_page()
            self.at_top = False
            offset, text = lines[index]
            if text:
                self.page.lines.append(
                    Line(self.x + offset, self.y, text, size, color, bold=bold)
                )
            self.y += leading
            index += 1
        self.y += definition["space_after"]
        self.at_top = False
        self.previous_space_after = definition["space_after"]

    def _group_height(self, group: Group) -> float:
        """Height a keep-together block needs where the column stands now."""
        total = 0.0
        previous_after = self.previous_space_after
        at_top = self.at_top
        for child in group.items:
            definition = page_style.style(child.style)
            lines = _wrap(
                child.text,
                definition["size"],
                self.width,
                definition["left_indent"],
                definition["first_line_indent"],
                self._font_for(definition),
                self.cjk,
            )
            total += (
                self._leading_space(definition, previous_after, at_top)
                + len(lines) * definition["leading"]
                + definition["space_after"]
            )
            previous_after = definition["space_after"]
            at_top = False
        return total

    def add(self, story: list[Item], *, paginate: bool = True) -> None:
        for item in story:
            if isinstance(item, Gap):
                self.y += item.height
                self.at_top = False
                self.previous_space_after = 0.0
            elif isinstance(item, Group):
                height = self._group_height(item)
                if paginate and self.y + height > self.bottom and self.y > self.top:
                    self._new_page()
                for child in item.items:
                    self._place(child, allow_split=paginate)
            else:
                self._place(item, allow_split=paginate)


def build_pages(data: dict[str, Any]) -> list[Page]:
    """Return every page of the CV as positioned lines."""
    locale = data.get("locale")
    # Measuring with the very font the export embeds is what keeps the preview
    # from drifting: a CJK CV wraps on screen exactly where the PDF wraps it.
    font = register_fonts(locale)
    bold_font = bold_font_for_locale(locale, font)
    cjk = is_cjk(locale)
    theme = themes.get_theme(data.get("theme"))
    sidebar_color = theme["color"]

    layout = layouts.get_layout(data.get("layout"))["key"]
    x, top, bottom, width = page_style.frame_geometry(layout)
    flow = _Flow(
        sidebar_color,
        top,
        page_style.PAGE_HEIGHT - bottom,
        x,
        width,
        font,
        bold_font,
        cjk,
        layout,
    )
    if layouts.is_single(layout):
        flow.add(single_column_story(data))
        return flow.pages

    flow.add(main_story(data))
    pages = flow.pages

    sidebar = _Flow(
        sidebar_color,
        page_style.SIDEBAR_TOP,
        page_style.PAGE_HEIGHT - page_style.MAIN_BOTTOM,
        page_style.SIDEBAR_X,
        page_style.SIDEBAR_TEXT_WIDTH,
        font,
        bold_font,
        cjk,
    )
    sidebar.add(sidebar_story(data), paginate=False)
    pages[0].lines.extend(sidebar.pages[0].lines)

    return pages
