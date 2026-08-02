"""Section 4 — education, and the hand-off to the preview step."""
from __future__ import annotations

import tkinter as tk
from typing import Any

from cv_builder.ui.components.fields import card, form_field, section_header
from cv_builder.ui.placeholders import PLACEHOLDERS
from cv_builder.ui.screens.sections.base import Section


class EducationSection(Section):
    def build(self) -> None:
        self.vars: dict[str, tk.StringVar] = {}
        section_header(
            self,
            self.fonts,
            step="Section 4 of 5",
            title="Education",
            subtitle="Add the qualification most relevant to this CV.",
            action_text="Preview  →",
            action_command=lambda: self.controller.show_section("preview"),
        )
        form = card(self)
        form.grid(row=1, column=0, sticky="new", padx=36, pady=(0, 30))
        form.grid_columnconfigure(0, weight=1)

        for key in ("institution", "qualification"):
            self.vars[key] = self.tracked_var()
        form_field(
            form,
            self.fonts,
            label="Institution",
            variable=self.vars["institution"],
            placeholder=PLACEHOLDERS["institution"],
            row=0,
            padx=22,
            pady=(22, 14),
        )
        form_field(
            form,
            self.fonts,
            label="Qualification and dates",
            variable=self.vars["qualification"],
            placeholder=PLACEHOLDERS["qualification"],
            row=1,
            padx=22,
            pady=(0, 22),
        )

    def collect(self, data: dict[str, Any]) -> None:
        for key, variable in self.vars.items():
            data["education"][key] = variable.get().strip()

    def populate(self, data: dict[str, Any]) -> None:
        for key, variable in self.vars.items():
            variable.set(data["education"].get(key, ""))
