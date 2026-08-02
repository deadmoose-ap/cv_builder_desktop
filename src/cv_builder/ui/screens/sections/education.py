"""Section 4 — education, and the hand-off to the preview step."""
from __future__ import annotations

import tkinter as tk
from typing import Any

from cv_builder.ui.components.fields import card, form_field, section_header
from cv_builder.ui.screens.sections.base import Section


class EducationSection(Section):
    def build(self) -> None:
        self.vars: dict[str, tk.StringVar] = {}
        section_header(
            self,
            self.fonts,
            step=self.step(4),
            title=self.t("education.title"),
            subtitle=self.t("education.subtitle"),
            action_text=self.t("education.action"),
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
            label=self.t("education.institution"),
            variable=self.vars["institution"],
            placeholder=self.placeholders["institution"],
            row=0,
            padx=22,
            pady=(22, 14),
        )
        form_field(
            form,
            self.fonts,
            label=self.t("education.qualification"),
            variable=self.vars["qualification"],
            placeholder=self.placeholders["qualification"],
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
