"""Section 2 — the professional summary."""
from __future__ import annotations

import tkinter as tk
from typing import Any

import customtkinter as ctk

from cv_builder.domain.text import split_paragraphs
from cv_builder.ui.components.fields import card, section_header, textbox
from cv_builder.ui.screens.sections.base import Section
from cv_builder.ui.theme import COLORS


class SummarySection(Section):
    def build(self) -> None:
        self.character_count = tk.StringVar(
            value=self.t("summary.character_count", count=0)
        )
        self.grid_rowconfigure(1, weight=1)
        section_header(
            self,
            self.fonts,
            step=self.step(2),
            title=self.t("summary.title"),
            subtitle=self.t("summary.subtitle"),
        )
        form = card(self)
        form.grid(row=1, column=0, sticky="nsew", padx=36, pady=(0, 30))
        form.grid_columnconfigure(0, weight=1)
        form.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(
            form,
            text=self.t("summary.label"),
            font=self.fonts.label,
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=22, pady=(22, 7))
        self.text = textbox(
            form,
            self.fonts,
            height=400,
            placeholder=self.placeholders["summary"],
        )
        self.text.grid(row=1, column=0, sticky="nsew", padx=22)
        self.text.bind("<KeyRelease>", self._on_typing, add="+")
        ctk.CTkLabel(
            form,
            textvariable=self.character_count,
            font=self.fonts.small,
            text_color=COLORS["muted"],
            anchor="e",
        ).grid(row=2, column=0, sticky="e", padx=22, pady=(8, 18))

    def _on_typing(self, _event=None) -> None:
        self.update_character_count()
        self.on_change()

    def update_character_count(self) -> None:
        count = len(self.text.get("1.0", "end-1c"))
        # A "Characters: N" label rather than a pluralised sentence: the nine
        # supported languages have three different plural systems between them.
        self.character_count.set(self.t("summary.character_count", count=count))

    def collect(self, data: dict[str, Any]) -> None:
        data["profile"]["summary"] = split_paragraphs(self.text.get("1.0", "end"))

    def populate(self, data: dict[str, Any]) -> None:
        self.text.set_value("\n\n".join(data["profile"].get("summary", [])))
        self.update_character_count()
