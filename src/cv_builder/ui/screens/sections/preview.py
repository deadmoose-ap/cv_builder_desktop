"""Section 5 — the final step: check every page and pick the sidebar colour."""
from __future__ import annotations

import tkinter as tk
from typing import Any

import customtkinter as ctk

from cv_builder.domain import locales, themes
from cv_builder.ui.components.fields import option_menu, section_header
from cv_builder.ui.components.preview_canvas import PreviewCanvas
from cv_builder.ui.screens.sections.base import Section
from cv_builder.ui.theme import COLORS


SWATCH_SIZE = 38
SWATCH_GAP = 8
SWATCHES_PER_ROW = 4
# Wide enough for the longest language label and four swatches on one row.
OPTIONS_WIDTH = 214


class PreviewSection(Section):
    """Document options on the left, the rendered pages on the right."""

    def build(self) -> None:
        self.theme_buttons: dict[str, ctk.CTkButton] = {}
        self.selected_theme = themes.DEFAULT_THEME
        self.selected_locale = locales.DEFAULT_LOCALE
        self.theme_label = tk.StringVar(value="")
        self.locale_label = tk.StringVar(value=locales.locale_label(None))
        self.document: dict[str, Any] | None = None

        # The options column keeps its width; the preview takes the rest, so
        # the pages start at the top of the step instead of below the controls.
        self.grid_rowconfigure(1, weight=1)
        section_header(
            self,
            self.fonts,
            step=self.step(5),
            title=self.t("preview.title"),
            subtitle=self.t("preview.subtitle"),
            action_text=self.t("editor.export_pdf"),
            action_command=self.controller.generate,
        )

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=(36, 24), pady=(0, 24))
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)
        self._build_options(body)
        self._build_stage(body)

    def _build_options(self, parent) -> None:
        options = ctk.CTkFrame(parent, fg_color="transparent", width=OPTIONS_WIDTH)
        options.grid(row=0, column=0, sticky="nsw", padx=(0, 24))
        options.grid_propagate(False)
        options.grid_columnconfigure(0, weight=1)
        self._build_locale_block(options)
        self._build_theme_block(options)

    def _caption(self, parent, row: int, label: str, hint, pady) -> None:
        ctk.CTkLabel(
            parent,
            text=label,
            font=self.fonts.small_bold,
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=row, column=0, sticky="ew", pady=pady)
        options = (
            {"textvariable": hint} if isinstance(hint, tk.StringVar) else {"text": hint}
        )
        ctk.CTkLabel(
            parent,
            font=self.fonts.small,
            text_color=COLORS["text"],
            anchor="w",
            justify="left",
            wraplength=OPTIONS_WIDTH,
            **options,
        ).grid(row=row + 1, column=0, sticky="ew", pady=(2, 8))

    def _build_locale_block(self, parent) -> None:
        """The CV's own language — independent of the interface language."""
        self._caption(
            parent,
            0,
            self.t("preview.cv_language"),
            self.t("preview.cv_language_hint"),
            (0, 0),
        )
        self.locale_menu = option_menu(
            parent,
            self.fonts,
            values=[locale["label"] for locale in locales.LOCALES],
            variable=self.locale_label,
            command=self._on_locale_selected,
            width=OPTIONS_WIDTH,
        )
        self.locale_menu.grid(row=2, column=0, sticky="ew")

    def _build_theme_block(self, parent) -> None:
        self._caption(
            parent,
            3,
            self.t("preview.sidebar_colour"),
            self.theme_label,
            (26, 0),
        )
        swatches = ctk.CTkFrame(parent, fg_color="transparent")
        swatches.grid(row=5, column=0, sticky="w")
        for index, theme in enumerate(themes.SIDEBAR_THEMES):
            swatch = ctk.CTkButton(
                swatches,
                text="",
                command=lambda key=theme["key"]: self.select_theme(key),
                width=SWATCH_SIZE,
                height=SWATCH_SIZE,
                corner_radius=8,
                fg_color=theme["color"],
                hover_color=theme["color"],
                border_width=2,
                border_color=COLORS["background"],
            )
            swatch.grid(
                row=index // SWATCHES_PER_ROW,
                column=index % SWATCHES_PER_ROW,
                padx=(0, SWATCH_GAP),
                pady=(0, SWATCH_GAP),
            )
            self.theme_buttons[theme["key"]] = swatch

    def _on_locale_selected(self, label: str) -> None:
        for locale in locales.LOCALES:
            if locale["label"] == label:
                self.select_locale(locale["code"])
                return

    def _build_stage(self, parent) -> None:
        stage = ctk.CTkFrame(parent, corner_radius=0, fg_color=COLORS["background"])
        stage.grid(row=0, column=1, sticky="nsew")
        stage.grid_columnconfigure(0, weight=1)
        stage.grid_rowconfigure(0, weight=1)
        self.canvas = PreviewCanvas(stage)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar = ctk.CTkScrollbar(
            stage,
            command=self.canvas.yview,
            fg_color="transparent",
            button_color=COLORS["border"],
            button_hover_color=COLORS["muted"],
        )
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(4, 0))
        self.canvas.configure(yscrollcommand=scrollbar.set)

    # --- state -----------------------------------------------------------

    def select_theme(self, key: str) -> None:
        self._highlight(key)
        if self.document is not None and self.document.get("theme") != key:
            self.document["theme"] = key
            self.on_change()
        self._redraw()

    def select_locale(self, code: str) -> None:
        """Set the language the CV's own section headings are printed in."""
        self._highlight_locale(code)
        if self.document is not None and self.document.get("locale") != code:
            self.document["locale"] = code
            self.on_change()
        self._redraw()

    def _highlight_locale(self, code: str) -> None:
        self.selected_locale = code
        self.locale_label.set(locales.locale_label(code))

    def _highlight(self, key: str) -> None:
        self.selected_theme = key
        # Colour names are interface copy, so they follow the interface
        # language rather than the CV's own locale.
        self.theme_label.set(self.t(f"theme.{key}"))
        for theme_key, swatch in self.theme_buttons.items():
            swatch.configure(
                border_color=(
                    COLORS["accent"] if theme_key == key else COLORS["background"]
                )
            )

    def populate(self, data: dict[str, Any]) -> None:
        self.document = data
        self._highlight(themes.get_theme(data.get("theme"))["key"])
        self._highlight_locale(locales.get_locale(data.get("locale"))["code"])

    def render_document(self, data: dict[str, Any]) -> None:
        """Draw the pages for the document as the form currently holds it."""
        self.document = data
        self._highlight(themes.get_theme(data.get("theme"))["key"])
        self._highlight_locale(locales.get_locale(data.get("locale"))["code"])
        self.update_idletasks()
        self._redraw()

    def _redraw(self) -> None:
        if self.document is not None:
            self.canvas.render(self.document)
