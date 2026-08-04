"""Month/year range picker for a position: start, end and "I work here now".

Two dropdowns per side rather than a calendar: a CV records months, and Tk has
no date widget that survives a PyInstaller bundle without a new dependency
([XPL], [LFO]). Month names come from `domain.dates` in the *interface*
language, because this is a hint addressed to the person filling the form; the
printed CV renders the same value in its own locale.
"""
from __future__ import annotations

import tkinter as tk
from datetime import date

import customtkinter as ctk

from cv_builder.domain.dates import MONTH_NAMES, make_ym, parse_ym
from cv_builder.ui.components.fields import checkbox, option_menu
from cv_builder.ui.theme import COLORS, Fonts


# A CV covers a working life, not history: one year ahead for a signed offer,
# sixty back for the earliest job worth listing.
YEARS_AHEAD = 1
YEARS_BACK = 60
EMPTY = "—"
MONTH_WIDTH = 150
YEAR_WIDTH = 100


def year_choices(today: date | None = None) -> list[str]:
    current = (today or date.today()).year
    return [str(year) for year in range(current + YEARS_AHEAD, current - YEARS_BACK, -1)]


class DateRangeField(ctk.CTkFrame):
    """Start and end month, with a checkbox that opens the range."""

    def __init__(
        self,
        parent,
        fonts: Fonts,
        *,
        translate,
        ui_locale: str | None = None,
        on_change=None,
    ):
        super().__init__(parent, fg_color="transparent")
        self.fonts = fonts
        self.t = translate
        self.months = MONTH_NAMES.get(ui_locale or "", MONTH_NAMES["en"])
        self.on_change = on_change
        self.years = year_choices()

        self.start_month = tk.StringVar(value=EMPTY)
        self.start_year = tk.StringVar(value=EMPTY)
        self.end_month = tk.StringVar(value=EMPTY)
        self.end_year = tk.StringVar(value=EMPTY)
        self.current = tk.BooleanVar(value=False)

        self.grid_columnconfigure(2, weight=1)
        self._build_side(0, "experience.date_start", self.start_month, self.start_year)
        self.end_menus = self._build_side(
            1, "experience.date_end", self.end_month, self.end_year
        )
        self.current_box = checkbox(
            self,
            fonts,
            text=self.t("experience.current"),
            variable=self.current,
            command=self._on_current_toggled,
        )
        self.current_box.grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 0))

    def _build_side(self, column: int, label_key: str, month, year) -> tuple:
        group = ctk.CTkFrame(self, fg_color="transparent")
        group.grid(
            row=0,
            column=column,
            sticky="w",
            padx=(0, 7) if column == 0 else (7, 0),
        )
        ctk.CTkLabel(
            group,
            text=self.t(label_key),
            font=self.fonts.label,
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))
        menus = []
        # Fixed widths on purpose: CTkOptionMenu draws its arrow at the width
        # it was configured with, so a stretched menu leaves the arrow stranded
        # in the middle of the field.
        for index, (variable, values, width) in enumerate(
            ((month, list(self.months), MONTH_WIDTH), (year, self.years, YEAR_WIDTH))
        ):
            menu = option_menu(
                group,
                self.fonts,
                values=[EMPTY, *values],
                variable=variable,
                command=lambda _value: self._notify(),
                width=width,
                height=40,
                fg_color=COLORS["surface_alt"],
            )
            menu.grid(
                row=1,
                column=index,
                sticky="w",
                padx=(0, 6) if index == 0 else (0, 0),
            )
            menus.append(menu)
        return tuple(menus)

    # --- state -----------------------------------------------------------

    def _notify(self) -> None:
        if self.on_change is not None:
            self.on_change()

    def _on_current_toggled(self) -> None:
        state = "disabled" if self.current.get() else "normal"
        if self.current.get():
            self.end_month.set(EMPTY)
            self.end_year.set(EMPTY)
        for menu in self.end_menus:
            menu.configure(state=state)
        self._notify()

    def _set_side(self, value: str, month: tk.StringVar, year: tk.StringVar) -> None:
        parsed = parse_ym(value)
        if parsed is None:
            month.set(EMPTY)
            year.set(EMPTY)
            return
        month.set(self.months[parsed[1] - 1])
        year.set(str(parsed[0]))

    def _read_side(self, month: tk.StringVar, year: tk.StringVar) -> str:
        name, value = month.get(), year.get()
        if name == EMPTY or value == EMPTY or name not in self.months:
            return ""
        return make_ym(int(value), self.months.index(name) + 1)

    def set_value(self, start: str, end: str, current: bool) -> None:
        self._set_side(start, self.start_month, self.start_year)
        self._set_side(end, self.end_month, self.end_year)
        self.current.set(bool(current))
        self._on_current_toggled()

    @property
    def start(self) -> str:
        return self._read_side(self.start_month, self.start_year)

    @property
    def end(self) -> str:
        return "" if self.current.get() else self._read_side(self.end_month, self.end_year)

    @property
    def is_current(self) -> bool:
        return bool(self.current.get())
