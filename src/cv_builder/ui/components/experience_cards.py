"""List rendering for the experience section: one card per company.

Kept out of `screens/sections/experience.py` so that file stays about state and
commands rather than widget layout ([SPL]).
"""
from __future__ import annotations

from typing import Any, Callable

import customtkinter as ctk

from cv_builder.domain import dates
from cv_builder.exporters.story import company_months, position_dates_line
from cv_builder.ui.components.fields import card
from cv_builder.ui.theme import COLORS, Fonts, button


def _icon_button(parent, fonts: Fonts, text: str, command, variant: str, width: int):
    return button(
        parent,
        fonts,
        text=text,
        command=command,
        variant=variant,
        width=width,
        height=30,
    )


def company_title(entry: dict[str, Any], fallback: str, ui_locale: str | None) -> str:
    """"Playrix (1 year 8 months)" — the tenure only once there is more than one role."""
    name = entry.get("company") or fallback
    positions = entry.get("positions") or []
    if len(positions) < 2:
        return name
    total = dates.format_duration(company_months(positions), ui_locale)
    return f"{name}  ({total})" if total else name


def position_meta(position: dict[str, Any], ui_locale: str | None) -> str:
    """The grey line under a position row: dates, duration and place."""
    parts = [position_dates_line(position, ui_locale), position.get("place", "")]
    return "  ·  ".join(part for part in parts if part)


def render_company_card(
    parent,
    fonts: Fonts,
    *,
    index: int,
    entry: dict[str, Any],
    translate: Callable[..., str],
    ui_locale: str | None,
    commands: dict[str, Callable],
) -> None:
    """One company: its header actions, then a row per position."""
    holder = card(parent)
    holder.grid(row=index, column=0, sticky="ew", padx=(0, 8), pady=(0, 10))
    holder.grid_columnconfigure(0, weight=1)

    header = ctk.CTkFrame(holder, fg_color="transparent")
    header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=18, pady=(16, 0))
    header.grid_columnconfigure(0, weight=1)
    ctk.CTkLabel(
        header,
        text=company_title(entry, translate("experience.no_company"), ui_locale),
        font=fonts.card_title,
        text_color=COLORS["text"],
        anchor="w",
    ).grid(row=0, column=0, sticky="w")

    actions = ctk.CTkFrame(header, fg_color="transparent")
    actions.grid(row=0, column=1, sticky="e")
    _icon_button(
        actions, fonts, translate("experience.action.edit"),
        lambda value=index: commands["edit_company"](value), "secondary", 56,
    ).pack(side="left", padx=(0, 4))
    _icon_button(
        actions, fonts, "↑", lambda value=index: commands["move_company"](-1, value),
        "ghost", 30,
    ).pack(side="left")
    _icon_button(
        actions, fonts, "↓", lambda value=index: commands["move_company"](1, value),
        "ghost", 30,
    ).pack(side="left")
    _icon_button(
        actions, fonts, translate("experience.action.delete"),
        lambda value=index: commands["delete_company"](value), "danger", 60,
    ).pack(side="left", padx=(3, 0))

    body = ctk.CTkFrame(holder, fg_color="transparent")
    body.grid(row=1, column=0, columnspan=2, sticky="ew", padx=18, pady=(10, 16))
    body.grid_columnconfigure(0, weight=1)

    positions = entry.get("positions") or []
    if not positions:
        ctk.CTkLabel(
            body,
            text=translate("experience.no_positions"),
            font=fonts.small,
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))
    for row, position in enumerate(positions):
        _render_position_row(
            body,
            fonts,
            row=row,
            company=index,
            position_index=row,
            position=position,
            translate=translate,
            ui_locale=ui_locale,
            commands=commands,
        )

    button(
        body,
        fonts,
        text=translate("experience.add_position"),
        command=lambda value=index: commands["add_position"](value),
        variant="secondary",
        width=170,
        height=32,
    ).grid(row=len(positions) + 1, column=0, sticky="w", pady=(4, 0))


def _render_position_row(
    parent,
    fonts: Fonts,
    *,
    row: int,
    company: int,
    position_index: int,
    position: dict[str, Any],
    translate: Callable[..., str],
    ui_locale: str | None,
    commands: dict[str, Callable],
) -> None:
    line = ctk.CTkFrame(parent, fg_color=COLORS["surface_alt"], corner_radius=9)
    line.grid(row=row, column=0, sticky="ew", pady=(0, 6))
    line.grid_columnconfigure(0, weight=1)

    text = ctk.CTkFrame(line, fg_color="transparent")
    text.grid(row=0, column=0, sticky="ew", padx=12, pady=9)
    text.grid_columnconfigure(0, weight=1)
    ctk.CTkLabel(
        text,
        text=position.get("role") or translate("experience.untitled_role"),
        font=fonts.body,
        text_color=COLORS["text"],
        anchor="w",
    ).grid(row=0, column=0, sticky="w")
    meta = position_meta(position, ui_locale)
    if meta:
        ctk.CTkLabel(
            text,
            text=meta,
            font=fonts.small,
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

    actions = ctk.CTkFrame(line, fg_color="transparent")
    actions.grid(row=0, column=1, sticky="e", padx=(6, 10))
    reference = (company, position_index)
    _icon_button(
        actions, fonts, translate("experience.action.edit"),
        lambda value=reference: commands["edit_position"](*value), "secondary", 56,
    ).pack(side="left", padx=(0, 4))
    _icon_button(
        actions, fonts, "↑",
        lambda value=reference: commands["move_position"](-1, *value), "ghost", 30,
    ).pack(side="left")
    _icon_button(
        actions, fonts, "↓",
        lambda value=reference: commands["move_position"](1, *value), "ghost", 30,
    ).pack(side="left")
    _icon_button(
        actions, fonts, translate("experience.action.delete"),
        lambda value=reference: commands["delete_position"](*value), "danger", 60,
    ).pack(side="left", padx=(3, 0))
