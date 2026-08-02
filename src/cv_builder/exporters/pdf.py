"""PDF rendering engine shared by the desktop app and tests."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Frame, KeepTogether, PageTemplate, Paragraph, Spacer

from cv_builder.domain import themes
from cv_builder.exporters import page_style
from cv_builder.exporters.story import Gap, Group, Para, main_story, sidebar_story


PAGE_WIDTH, PAGE_HEIGHT = letter
SIDEBAR_WIDTH = page_style.SIDEBAR_WIDTH
MAIN_X = page_style.MAIN_X
MAIN_WIDTH = page_style.MAIN_WIDTH


def _resource_path(relative: str) -> Path:
    """Resolve bundled resources in development and PyInstaller builds."""
    # src/cv_builder/exporters/pdf.py -> project root during development.
    project_root = Path(__file__).resolve().parents[3]
    base = Path(getattr(sys, "_MEIPASS", project_root))
    return base / relative


def _font_candidates(bold: bool) -> list[Path]:
    bundled = _resource_path("assets/Arial Bold.ttf" if bold else "assets/Arial.ttf")
    if sys.platform == "darwin":
        system = Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf")
    elif os.name == "nt":
        windows = Path(os.environ.get("WINDIR", "C:/Windows"))
        system = windows / "Fonts" / ("arialbd.ttf" if bold else "arial.ttf")
    else:
        system = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    return [bundled, system]


def _find_font(bold: bool) -> Path:
    for candidate in _font_candidates(bold):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("No supported Arial or DejaVu Sans font was found.")


def register_fonts() -> None:
    """Register the CV fonts once per process; safe to call repeatedly."""
    if "CVRegular" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("CVRegular", str(_find_font(False))))
        pdfmetrics.registerFont(TTFont("CVBold", str(_find_font(True))))


_register_fonts = register_fonts


def _safe(value: Any) -> str:
    return escape(str(value or "")).replace("\n", "<br/>")


def _styles(sidebar_color: str) -> dict[str, ParagraphStyle]:
    styles = {}
    for name in page_style.STYLES:
        definition = page_style.style(name)
        styles[name] = ParagraphStyle(
            name,
            fontName="CVRegular",
            fontSize=definition["size"],
            leading=definition["leading"],
            spaceBefore=definition["space_before"],
            spaceAfter=definition["space_after"],
            leftIndent=definition["left_indent"],
            firstLineIndent=definition["first_line_indent"],
            textColor=colors.HexColor(page_style.resolve_color(name, sidebar_color)),
        )
    return styles


def generate_pdf(data: dict[str, Any], output_path: str | Path) -> None:
    """Generate a polished CV PDF from a validated data dictionary."""
    register_fonts()
    theme = themes.get_theme(data.get("theme"))
    sidebar_color = theme["color"]
    styles = _styles(sidebar_color)
    profile = data["profile"]

    def flowables(items) -> list:
        result = []
        for item in items:
            if isinstance(item, Gap):
                result.append(Spacer(1, item.height))
            elif isinstance(item, Group):
                result.append(KeepTogether(flowables(item.items)))
            else:
                result.append(Paragraph(_safe(item.text), styles[item.style]))
        return result

    def page_decoration(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(colors.HexColor(sidebar_color))
        canvas.rect(0, 0, SIDEBAR_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
        if doc.page == 1:
            y = PAGE_HEIGHT - page_style.SIDEBAR_TOP
            for item in flowables(sidebar_story(profile)):
                _, height = item.wrap(page_style.SIDEBAR_TEXT_WIDTH, y)
                y -= height
                item.drawOn(canvas, page_style.SIDEBAR_X, y)
                y -= 2
        canvas.setFont("CVRegular", page_style.PAGE_NUMBER_SIZE)
        canvas.setFillColor(colors.HexColor(page_style.PAGE_NUMBER_COLOR))
        canvas.drawRightString(
            PAGE_WIDTH - page_style.PAGE_NUMBER_RIGHT,
            page_style.PAGE_NUMBER_BOTTOM,
            f"Page {doc.page}",
        )
        canvas.restoreState()

    document = BaseDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=MAIN_X,
        rightMargin=34,
        topMargin=page_style.MAIN_TOP,
        bottomMargin=page_style.MAIN_BOTTOM,
    )
    frame = Frame(
        MAIN_X,
        page_style.MAIN_BOTTOM,
        MAIN_WIDTH,
        PAGE_HEIGHT - page_style.MAIN_TOP - page_style.MAIN_BOTTOM,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )
    document.addPageTemplates([PageTemplate(id="cv", frames=[frame], onPage=page_decoration)])
    document.build(flowables(main_story(data)))
