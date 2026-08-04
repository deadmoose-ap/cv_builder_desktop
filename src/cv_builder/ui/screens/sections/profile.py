"""Section 1 — profile details and core skills."""
from __future__ import annotations

import tkinter as tk
from typing import Any

import customtkinter as ctk

from cv_builder.domain.text import split_lines
from cv_builder.ui.components.fields import card, form_field, section_header, textbox
from cv_builder.ui.screens.sections.base import Section
from cv_builder.ui.theme import COLORS


FIELDS = ("name", "headline", "location", "email", "linkedin")


class ProfileSection(Section):
    def build(self) -> None:
        self.vars: dict[str, tk.StringVar] = {}
        self.entries: dict[str, Any] = {}
        placeholders = self.placeholders
        section_header(
            self,
            self.fonts,
            step=self.step(1),
            title=self.t("profile.title"),
            subtitle=self.t("profile.subtitle"),
        )
        form = card(self)
        form.grid(row=1, column=0, sticky="new", padx=36, pady=(0, 30))
        form.grid_columnconfigure((0, 1), weight=1, uniform="profile")

        for key in FIELDS:
            self.vars[key] = self.tracked_var()

        self.entries["name"] = form_field(
            form,
            self.fonts,
            label=self.t("profile.name"),
            variable=self.vars["name"],
            placeholder=placeholders["name"],
            row=0,
            columnspan=2,
            padx=22,
            pady=(22, 14),
        )
        self.entries["headline"] = form_field(
            form,
            self.fonts,
            label=self.t("profile.headline"),
            variable=self.vars["headline"],
            placeholder=placeholders["headline"],
            row=1,
            columnspan=2,
            padx=22,
        )
        self.entries["location"] = form_field(
            form,
            self.fonts,
            label=self.t("profile.location"),
            variable=self.vars["location"],
            placeholder=placeholders["location"],
            row=2,
            column=0,
            padx=(22, 7),
        )
        self.entries["email"] = form_field(
            form,
            self.fonts,
            label=self.t("profile.email"),
            variable=self.vars["email"],
            placeholder=placeholders["email"],
            row=2,
            column=1,
            padx=(7, 22),
        )
        self.entries["linkedin"] = form_field(
            form,
            self.fonts,
            label=self.t("profile.linkedin"),
            variable=self.vars["linkedin"],
            placeholder=placeholders["linkedin"],
            row=3,
            columnspan=2,
            padx=22,
        )

        # Two short one-per-line lists sharing a row: side by side they cost no
        # more height than skills alone used to.
        self.skills_text = self._list_group(
            form, "skills", column=0, padx=(22, 7)
        )
        self.languages_text = self._list_group(
            form, "languages", column=1, padx=(7, 22)
        )

    def _list_group(self, form, key: str, *, column: int, padx) -> Any:
        """A labelled one-item-per-line textbox, as used for skills."""
        group = ctk.CTkFrame(form, fg_color="transparent")
        group.grid(row=4, column=column, sticky="ew", padx=padx, pady=(0, 22))
        group.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            group,
            text=self.t(f"profile.{key}"),
            font=self.fonts.label,
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            group,
            text=self.t(f"profile.{key}_hint"),
            font=self.fonts.small,
            text_color=COLORS["muted"],
            anchor="e",
        ).grid(row=0, column=1, sticky="e")
        widget = textbox(
            group,
            self.fonts,
            height=118,
            placeholder=self.placeholders[key],
        )
        widget.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        widget.bind("<KeyRelease>", lambda _event: self.on_change(), add="+")
        return widget

    def collect(self, data: dict[str, Any]) -> None:
        profile = data["profile"]
        for key, variable in self.vars.items():
            profile[key] = variable.get().strip()
        profile["skills"] = split_lines(self.skills_text.get("1.0", "end"))
        profile["languages"] = split_lines(self.languages_text.get("1.0", "end"))

    def populate(self, data: dict[str, Any]) -> None:
        profile = data["profile"]
        for key, variable in self.vars.items():
            variable.set(profile.get(key, ""))
        self.skills_text.set_value("\n".join(profile.get("skills", [])))
        self.languages_text.set_value("\n".join(profile.get("languages", [])))
