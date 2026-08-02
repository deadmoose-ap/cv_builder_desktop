"""Section 1 — profile details and core skills."""
from __future__ import annotations

import tkinter as tk
from typing import Any

import customtkinter as ctk

from cv_builder.domain.text import split_lines
from cv_builder.ui.components.fields import card, form_field, section_header, textbox
from cv_builder.ui.placeholders import PLACEHOLDERS
from cv_builder.ui.screens.sections.base import Section
from cv_builder.ui.theme import COLORS


FIELDS = ("name", "headline", "location", "email", "linkedin")


class ProfileSection(Section):
    def build(self) -> None:
        self.vars: dict[str, tk.StringVar] = {}
        self.entries: dict[str, Any] = {}
        section_header(
            self,
            self.fonts,
            step="Section 1 of 5",
            title="Profile",
            subtitle="The essential details shown at the top of your CV.",
        )
        form = card(self)
        form.grid(row=1, column=0, sticky="new", padx=36, pady=(0, 30))
        form.grid_columnconfigure((0, 1), weight=1, uniform="profile")

        for key in FIELDS:
            self.vars[key] = self.tracked_var()

        self.entries["name"] = form_field(
            form,
            self.fonts,
            label="Full name",
            variable=self.vars["name"],
            placeholder=PLACEHOLDERS["name"],
            row=0,
            columnspan=2,
            padx=22,
            pady=(22, 14),
        )
        self.entries["headline"] = form_field(
            form,
            self.fonts,
            label="Professional headline",
            variable=self.vars["headline"],
            placeholder=PLACEHOLDERS["headline"],
            row=1,
            columnspan=2,
            padx=22,
        )
        self.entries["location"] = form_field(
            form,
            self.fonts,
            label="Location",
            variable=self.vars["location"],
            placeholder=PLACEHOLDERS["location"],
            row=2,
            column=0,
            padx=(22, 7),
        )
        self.entries["email"] = form_field(
            form,
            self.fonts,
            label="Email",
            variable=self.vars["email"],
            placeholder=PLACEHOLDERS["email"],
            row=2,
            column=1,
            padx=(7, 22),
        )
        self.entries["linkedin"] = form_field(
            form,
            self.fonts,
            label="LinkedIn or website",
            variable=self.vars["linkedin"],
            placeholder=PLACEHOLDERS["linkedin"],
            row=3,
            columnspan=2,
            padx=22,
        )

        skills_group = ctk.CTkFrame(form, fg_color="transparent")
        skills_group.grid(
            row=4,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=22,
            pady=(0, 22),
        )
        skills_group.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            skills_group,
            text="Core skills",
            font=self.fonts.label,
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            skills_group,
            text="One skill per line",
            font=self.fonts.small,
            text_color=COLORS["muted"],
            anchor="e",
        ).grid(row=0, column=1, sticky="e")
        self.skills_text = textbox(
            skills_group,
            self.fonts,
            height=118,
            placeholder=PLACEHOLDERS["skills"],
        )
        self.skills_text.grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0)
        )
        self.skills_text.bind(
            "<KeyRelease>", lambda _event: self.on_change(), add="+"
        )

    def collect(self, data: dict[str, Any]) -> None:
        profile = data["profile"]
        for key, variable in self.vars.items():
            profile[key] = variable.get().strip()
        profile["skills"] = split_lines(self.skills_text.get("1.0", "end"))

    def populate(self, data: dict[str, Any]) -> None:
        profile = data["profile"]
        for key, variable in self.vars.items():
            variable.set(profile.get(key, ""))
        self.skills_text.set_value("\n".join(profile.get("skills", [])))
