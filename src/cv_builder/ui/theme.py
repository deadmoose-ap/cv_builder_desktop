"""Interface tokens: colours, fonts and the button variants.

Explicit tokens only — never rely on platform defaults ([XPL]). Screens read
their colours and fonts from here instead of hard-coding values.
"""
from __future__ import annotations

from tkinter import font as tkfont

import customtkinter as ctk


COLORS = {
    "background": "#F6F7FB",
    "surface": "#FFFFFF",
    "surface_alt": "#EFF3F8",
    "text": "#172033",
    "muted": "#667085",
    "border": "#D7DDE8",
    "accent": "#2F6BFF",
    "accent_hover": "#2457D6",
    "selection": "#EAF0FF",
    "danger": "#B42318",
    "danger_hover": "#FDECEC",
    "success": "#127A45",
}


# CustomTkinter's own theme asks for "SF Display" on macOS and "Roboto" on
# Windows; neither carries a single CJK glyph, so an interface switched to
# Japanese, Korean or Chinese would render as empty boxes. Each locale lists
# the system families to try, best first.
UI_FONT_FAMILIES = {
    "ja": ("Hiragino Sans", "Yu Gothic UI", "Meiryo UI", "Arial Unicode MS"),
    "ko": ("Apple SD Gothic Neo", "Malgun Gothic", "Arial Unicode MS"),
    "zh-Hans": ("PingFang SC", "Microsoft YaHei UI", "Heiti SC", "Arial Unicode MS"),
    "zh-Hant": ("PingFang TC", "Microsoft JhengHei UI", "Heiti TC", "Arial Unicode MS"),
}


def ui_font_family(locale: str | None) -> str | None:
    """First installed family that can draw this locale, or the CTk default."""
    candidates = UI_FONT_FAMILIES.get(locale or "")
    if not candidates:
        return None
    installed = set(tkfont.families())
    return next((name for name in candidates if name in installed), None)


class Fonts:
    """Named fonts, created once a Tk root exists."""

    def __init__(self, locale: str | None = None):
        self.locale = locale
        family = ui_font_family(locale)
        # `family=None` keeps CustomTkinter's platform default for Latin and
        # Cyrillic, so those interfaces look exactly as they did before.
        def font(size: int, weight: str = "normal") -> ctk.CTkFont:
            if family is None:
                return ctk.CTkFont(size=size, weight=weight)
            return ctk.CTkFont(family=family, size=size, weight=weight)

        self.brand = font(17, "bold")
        self.body = font(13)
        self.button = font(13)
        self.button_bold = font(13, "bold")
        self.small = font(12)
        self.small_bold = font(11, "bold")
        self.label = font(13, "bold")
        self.card_title = font(15, "bold")
        self.page_title = font(26, "bold")
        self.nav = font(14)
        self.nav_active = font(14, "bold")
        # Icon glyphs need their own size: at body size a ⚙ reads as a speck.
        self.gear = ctk.CTkFont(size=21)


def button(
    parent,
    fonts: Fonts,
    *,
    text: str,
    command,
    variant: str = "secondary",
    width: int = 84,
    height: int = 38,
    anchor: str = "center",
) -> ctk.CTkButton:
    """Create one of the four approved button variants."""
    common = {
        "text": text,
        "command": command,
        "width": width,
        "height": height,
        "corner_radius": 8,
        "font": fonts.button,
        "anchor": anchor,
        "border_spacing": 5,
    }
    variants = {
        "primary": {
            "fg_color": COLORS["accent"],
            "hover_color": COLORS["accent_hover"],
            "text_color": "#FFFFFF",
            "font": fonts.button_bold,
        },
        "secondary": {
            "fg_color": COLORS["surface"],
            "hover_color": COLORS["selection"],
            "text_color": COLORS["text"],
            "border_width": 1,
            "border_color": COLORS["border"],
        },
        "ghost": {
            "fg_color": "transparent",
            "hover_color": COLORS["surface_alt"],
            "text_color": COLORS["muted"],
        },
        "danger": {
            "fg_color": "transparent",
            "hover_color": COLORS["danger_hover"],
            "text_color": COLORS["danger"],
        },
    }
    common.update(variants[variant])
    return ctk.CTkButton(parent, **common)
