"""Interface tokens: colours, fonts and the button variants.

Explicit tokens only — never rely on platform defaults ([XPL]). Screens read
their colours and fonts from here instead of hard-coding values.
"""
from __future__ import annotations

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


class Fonts:
    """Named fonts, created once a Tk root exists."""

    def __init__(self):
        self.brand = ctk.CTkFont(size=17, weight="bold")
        self.body = ctk.CTkFont(size=13)
        self.button = ctk.CTkFont(size=13, weight="normal")
        self.button_bold = ctk.CTkFont(size=13, weight="bold")
        self.small = ctk.CTkFont(size=12)
        self.small_bold = ctk.CTkFont(size=11, weight="bold")
        self.label = ctk.CTkFont(size=13, weight="bold")
        self.card_title = ctk.CTkFont(size=15, weight="bold")
        self.page_title = ctk.CTkFont(size=26, weight="bold")
        self.nav = ctk.CTkFont(size=14)
        self.nav_active = ctk.CTkFont(size=14, weight="bold")


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
