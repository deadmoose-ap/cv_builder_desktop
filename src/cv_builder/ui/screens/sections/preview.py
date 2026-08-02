"""Section 5 — the final step: check every page and pick the sidebar colour."""
from __future__ import annotations

import tkinter as tk
from typing import Any

import customtkinter as ctk

from cv_builder.domain import themes
from cv_builder.ui.components.fields import section_header
from cv_builder.ui.components.preview_canvas import PreviewCanvas
from cv_builder.ui.screens.sections.base import Section
from cv_builder.ui.theme import COLORS


SWATCH_WIDTH = 62
SWATCH_HEIGHT = 34


class PreviewSection(Section):
    """Read-only render of the whole CV plus the colour picker."""

    def build(self) -> None:
        self.theme_buttons: dict[str, ctk.CTkButton] = {}
        self.selected_theme = themes.DEFAULT_THEME
        self.theme_label = tk.StringVar(value="")
        self.document: dict[str, Any] | None = None

        self.grid_rowconfigure(2, weight=1)
        section_header(
            self,
            self.fonts,
            step="Section 5 of 5",
            title="Preview",
            subtitle="Check every page and choose the sidebar colour before exporting.",
            action_text="Export PDF",
            action_command=self.controller.generate,
        )
        self._build_theme_row()
        self._build_stage()

    def _build_theme_row(self) -> None:
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.grid(row=1, column=0, sticky="ew", padx=36, pady=(0, 14))
        row.grid_columnconfigure(1, weight=1)

        caption = ctk.CTkFrame(row, fg_color="transparent")
        caption.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        ctk.CTkLabel(
            caption,
            text="SIDEBAR COLOUR",
            font=self.fonts.small_bold,
            text_color=COLORS["muted"],
            anchor="w",
        ).pack(side="left")
        ctk.CTkLabel(
            caption,
            textvariable=self.theme_label,
            font=self.fonts.small,
            text_color=COLORS["text"],
            anchor="w",
        ).pack(side="left", padx=(10, 0))

        swatches = ctk.CTkFrame(row, fg_color="transparent")
        swatches.grid(row=1, column=0, columnspan=2, sticky="w")
        for theme in themes.SIDEBAR_THEMES:
            swatch = ctk.CTkButton(
                swatches,
                text="",
                command=lambda key=theme["key"]: self.select_theme(key),
                width=SWATCH_WIDTH,
                height=SWATCH_HEIGHT,
                corner_radius=8,
                fg_color=theme["color"],
                hover_color=theme["color"],
                border_width=2,
                border_color=COLORS["background"],
            )
            swatch.pack(side="left", padx=(0, 8))
            self.theme_buttons[theme["key"]] = swatch

    def _build_stage(self) -> None:
        stage = ctk.CTkFrame(self, corner_radius=0, fg_color=COLORS["background"])
        stage.grid(row=2, column=0, sticky="nsew", padx=(36, 24), pady=(0, 24))
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

    def _highlight(self, key: str) -> None:
        self.selected_theme = key
        self.theme_label.set(themes.get_theme(key)["label"])
        for theme_key, swatch in self.theme_buttons.items():
            swatch.configure(
                border_color=(
                    COLORS["accent"] if theme_key == key else COLORS["background"]
                )
            )

    def populate(self, data: dict[str, Any]) -> None:
        self.document = data
        self._highlight(themes.get_theme(data.get("theme"))["key"])

    def render_document(self, data: dict[str, Any]) -> None:
        """Draw the pages for the document as the form currently holds it."""
        self.document = data
        self._highlight(themes.get_theme(data.get("theme"))["key"])
        self.update_idletasks()
        self._redraw()

    def _redraw(self) -> None:
        if self.document is not None:
            self.canvas.render(self.document)
