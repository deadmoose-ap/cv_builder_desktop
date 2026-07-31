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


PAGE_WIDTH, PAGE_HEIGHT = letter
SIDEBAR_WIDTH = 202
MAIN_X = 223
MAIN_WIDTH = 355


def _resource_path(relative: str) -> Path:
    """Resolve bundled resources in development and PyInstaller builds."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
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


def _register_fonts() -> None:
    if "CVRegular" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("CVRegular", str(_find_font(False))))
        pdfmetrics.registerFont(TTFont("CVBold", str(_find_font(True))))


def _safe(value: Any) -> str:
    return escape(str(value or "")).replace("\n", "<br/>")


def _styles() -> dict[str, ParagraphStyle]:
    return {
        "name": ParagraphStyle("name", fontName="CVRegular", fontSize=28, leading=32, spaceAfter=7),
        "headline": ParagraphStyle("headline", fontName="CVRegular", fontSize=12.6, leading=15.5, spaceAfter=2),
        "location": ParagraphStyle("location", fontName="CVRegular", fontSize=12, leading=15, textColor=colors.HexColor("#a9a9a9"), spaceAfter=20),
        "section": ParagraphStyle("section", fontName="CVRegular", fontSize=17, leading=21, spaceBefore=11, spaceAfter=10),
        "company": ParagraphStyle("company", fontName="CVRegular", fontSize=12, leading=15, spaceAfter=3),
        "duration": ParagraphStyle("duration", fontName="CVRegular", fontSize=10.5, leading=13.5, spaceAfter=7),
        "role": ParagraphStyle("role", fontName="CVRegular", fontSize=12, leading=15, spaceAfter=1),
        "dates": ParagraphStyle("dates", fontName="CVRegular", fontSize=10.5, leading=13, spaceAfter=7),
        "body": ParagraphStyle("body", fontName="CVRegular", fontSize=10.5, leading=15.1, spaceAfter=9),
        "bullet": ParagraphStyle("bullet", fontName="CVRegular", fontSize=10.5, leading=14.5, leftIndent=12, firstLineIndent=-9, spaceAfter=3),
        "side_head": ParagraphStyle("side_head", fontName="CVRegular", fontSize=14, leading=18, textColor=colors.HexColor("#e8ebed"), spaceAfter=6),
        "side_body": ParagraphStyle("side_body", fontName="CVRegular", fontSize=10.5, leading=15, textColor=colors.white, spaceAfter=7),
    }


def generate_pdf(data: dict[str, Any], output_path: str | Path) -> None:
    """Generate a polished CV PDF from a validated data dictionary."""
    _register_fonts()
    styles = _styles()
    profile = data["profile"]

    def p(text: Any, style: str = "body", markup: bool = False) -> Paragraph:
        return Paragraph(str(text) if markup else _safe(text), styles[style])

    def page_decoration(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(colors.HexColor("#29414c"))
        canvas.rect(0, 0, SIDEBAR_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
        if doc.page == 1:
            sidebar = [
                p("CONTACT", "side_head"), p(profile.get("email", ""), "side_body"),
                p(profile.get("linkedin", ""), "side_body"), Spacer(1, 12),
                p("CORE SKILLS", "side_head"),
                p("<br/>".join(_safe(v) for v in profile.get("skills", [])), "side_body", markup=True),
            ]
            y = PAGE_HEIGHT - 43
            for item in sidebar:
                _, height = item.wrap(150, y)
                y -= height
                item.drawOn(canvas, 22, y)
                y -= 2
        canvas.setFont("CVRegular", 9)
        canvas.setFillColor(colors.HexColor("#1d1d1d"))
        canvas.drawRightString(PAGE_WIDTH - 30, 18, f"Page {doc.page}")
        canvas.restoreState()

    document = BaseDocTemplate(str(output_path), pagesize=letter, leftMargin=MAIN_X, rightMargin=34, topMargin=40, bottomMargin=38)
    frame = Frame(MAIN_X, 38, MAIN_WIDTH, PAGE_HEIGHT - 78, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    document.addPageTemplates([PageTemplate(id="cv", frames=[frame], onPage=page_decoration)])

    story = [p(profile.get("name", ""), "name"), p(profile.get("headline", ""), "headline"), p(profile.get("location", ""), "location"), p("SUMMARY", "section")]
    story += [p(value) for value in profile.get("summary", []) if value.strip()]
    story += [p("EXPERIENCE", "section")]

    for item in data.get("experience", []):
        header = [p(item.get("company", ""), "company")]
        if item.get("duration"):
            header.append(p(item["duration"], "duration"))
        header += [p(item.get("role", ""), "role"), p(item.get("dates", ""), "dates")]
        if item.get("place"):
            header.append(p(item["place"], "dates"))
        story.append(KeepTogether(header))
        if item.get("intro"):
            story += [Spacer(1, 5), p(item["intro"])]
        for label, key in (("KEY RESPONSIBILITIES", "work"), ("RESULTS", "results")):
            values = [value for value in item.get(key, []) if value.strip()]
            if values:
                story.append(p(f"{label}:<br/>&bull; {_safe(values[0])}", markup=True))
                story += [p(f"&bull; {_safe(value)}", "bullet", markup=True) for value in values[1:]]
        story.append(Spacer(1, 12))

    education = data.get("education", {})
    story += [p("EDUCATION", "section"), p(education.get("institution", ""), "company"), p(education.get("qualification", ""), "dates")]
    document.build(story)
