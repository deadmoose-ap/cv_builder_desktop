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
from cv_builder.domain.cv_labels import page_label
from cv_builder.domain.locales import CJK_LOCALES, is_cjk
from cv_builder.exporters import page_style
from cv_builder.exporters.story import Gap, Group, Para, main_story, sidebar_story


PAGE_WIDTH, PAGE_HEIGHT = letter
SIDEBAR_WIDTH = page_style.SIDEBAR_WIDTH
MAIN_X = page_style.MAIN_X
MAIN_WIDTH = page_style.MAIN_WIDTH

# Arial covers Latin and Cyrillic but contains no CJK glyph at all, so those
# locales need their own face. Each entry is the bundled file plus the system
# fonts to fall back on when the bundle is missing (a source checkout without
# assets/, or a stripped install).
CJK_FONTS: dict[str, dict[str, Any]] = {
    "ja": {
        "bundled": "assets/fonts/NotoSansJP-Regular.ttf",
        "darwin": ["/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc", "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"],
        "nt": ["YuGothR.ttc", "meiryo.ttc", "msgothic.ttc"],
    },
    "ko": {
        "bundled": "assets/fonts/NotoSansKR-Regular.ttf",
        "darwin": ["/System/Library/Fonts/AppleSDGothicNeo.ttc", "/System/Library/Fonts/Supplemental/AppleGothic.ttf"],
        "nt": ["malgun.ttf", "gulim.ttc"],
    },
    "zh-Hans": {
        "bundled": "assets/fonts/NotoSansSC-Regular.ttf",
        "darwin": ["/System/Library/Fonts/STHeiti Light.ttc", "/System/Library/Fonts/Hiragino Sans GB.ttc"],
        "nt": ["msyh.ttc", "simhei.ttf"],
    },
    "zh-Hant": {
        "bundled": "assets/fonts/NotoSansTC-Regular.ttf",
        "darwin": ["/System/Library/Fonts/Supplemental/Songti.ttc", "/System/Library/Fonts/STHeiti Light.ttc"],
        "nt": ["msjh.ttc", "mingliu.ttc"],
    },
}
LATIN_FONT = "CVRegular"


def _resource_path(relative: str) -> Path:
    """Resolve bundled resources in development and PyInstaller builds."""
    # src/cv_builder/exporters/pdf.py -> project root during development.
    project_root = Path(__file__).resolve().parents[3]
    base = Path(getattr(sys, "_MEIPASS", project_root))
    return base / relative


def _windows_fonts() -> Path:
    return Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"


def _font_candidates(bold: bool) -> list[Path]:
    bundled = _resource_path("assets/Arial Bold.ttf" if bold else "assets/Arial.ttf")
    if sys.platform == "darwin":
        system = Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf")
    elif os.name == "nt":
        system = _windows_fonts() / ("arialbd.ttf" if bold else "arial.ttf")
    else:
        system = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    return [bundled, system]


def _cjk_candidates(locale: str) -> list[Path]:
    definition = CJK_FONTS[locale]
    candidates = [_resource_path(definition["bundled"])]
    if sys.platform == "darwin":
        candidates += [Path(value) for value in definition["darwin"]]
    elif os.name == "nt":
        candidates += [_windows_fonts() / value for value in definition["nt"]]
    return candidates


def _find_font(bold: bool) -> Path:
    for candidate in _font_candidates(bold):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("No supported Arial or DejaVu Sans font was found.")


def font_for_locale(locale: str | None) -> str:
    """Return the registered font name a CV in this locale must be set in."""
    return f"CVRegular-{locale}" if locale in CJK_FONTS else LATIN_FONT


def register_fonts(locale: str | None = None) -> str:
    """Register the fonts this locale needs; safe to call repeatedly.

    Registration is tracked per font name rather than once per process, so a
    session that exports an English CV and then a Japanese one registers both.
    """
    registered = pdfmetrics.getRegisteredFontNames()
    if LATIN_FONT not in registered:
        pdfmetrics.registerFont(TTFont(LATIN_FONT, str(_find_font(False))))
        pdfmetrics.registerFont(TTFont("CVBold", str(_find_font(True))))
    name = font_for_locale(locale)
    if name == LATIN_FONT or name in registered:
        return name
    for candidate in _cjk_candidates(str(locale)):
        if not candidate.is_file():
            continue
        try:
            pdfmetrics.registerFont(TTFont(name, str(candidate)))
        except Exception:
            # Some system faces are OpenType/CFF collections ReportLab cannot
            # read; keep looking instead of failing the whole export.
            continue
        return name
    # Nothing usable: Latin text still renders, CJK text becomes blank boxes.
    # Better a readable partial document than a failed export.
    return LATIN_FONT


_register_fonts = register_fonts


def _safe(value: Any) -> str:
    return escape(str(value or "")).replace("\n", "<br/>")


def _styles(sidebar_color: str, font_name: str, cjk: bool) -> dict[str, ParagraphStyle]:
    styles = {}
    for name in page_style.STYLES:
        definition = page_style.style(name)
        styles[name] = ParagraphStyle(
            name,
            fontName=font_name,
            # Japanese, Korean and Chinese are written without spaces, so the
            # default whitespace-based wrapping would run a whole paragraph
            # off the page as one unbreakable "word".
            wordWrap="CJK" if cjk else None,
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
    locale = data.get("locale")
    font_name = register_fonts(locale)
    theme = themes.get_theme(data.get("theme"))
    sidebar_color = theme["color"]
    styles = _styles(sidebar_color, font_name, is_cjk(locale))

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
            for item in flowables(sidebar_story(data)):
                _, height = item.wrap(page_style.SIDEBAR_TEXT_WIDTH, y)
                y -= height
                item.drawOn(canvas, page_style.SIDEBAR_X, y)
                y -= 2
        canvas.setFont(font_name, page_style.PAGE_NUMBER_SIZE)
        canvas.setFillColor(colors.HexColor(page_style.PAGE_NUMBER_COLOR))
        canvas.drawRightString(
            PAGE_WIDTH - page_style.PAGE_NUMBER_RIGHT,
            page_style.PAGE_NUMBER_BOTTOM,
            page_label(locale, doc.page),
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
