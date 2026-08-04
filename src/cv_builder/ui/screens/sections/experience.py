"""Section 3 — companies, each holding the positions held there.

Two levels, because a career track happens inside one employer: the list shows
one card per company with a row per position, and the inline editor switches
between a company form and a position form.
"""
from __future__ import annotations

import tkinter as tk
from copy import deepcopy
from tkinter import messagebox
from typing import Any

import customtkinter as ctk

from cv_builder.domain.dates import parse_ym
from cv_builder.domain.model import empty_experience, empty_position
from cv_builder.domain.text import split_lines
from cv_builder.ui.components.date_range import DateRangeField
from cv_builder.ui.components.experience_cards import render_company_card
from cv_builder.ui.components.fields import card, form_field, section_header, textbox
from cv_builder.ui.components.scrollable import AutoHideScrollableFrame
from cv_builder.ui.screens.sections.base import Section
from cv_builder.ui.theme import COLORS, button


# (translation key, document key, textbox height, needs the one-per-line hint)
TEXT_FIELDS = (
    ("experience.intro", "intro", 72, False),
    ("experience.work", "work", 94, True),
    ("experience.results", "results", 86, True),
)


class ExperienceSection(Section):
    def build(self) -> None:
        self.document: dict[str, Any] = {"experience": []}
        self.editor_texts: dict[str, Any] = {}
        # (company index, position index or None) currently being edited, and
        # None while nothing is open.
        self.editing: tuple[int | None, int | None] | None = None
        self.selection: int | None = None
        self.editor_open = False
        self.title = tk.StringVar(value=self.t("experience.title"))
        self.subtitle = tk.StringVar(value=self.t("experience.subtitle"))
        self.company_var = tk.StringVar()
        self.role_var = tk.StringVar()
        self.place_var = tk.StringVar()

        self.grid_rowconfigure(1, weight=1)
        self.add_button = section_header(
            self,
            self.fonts,
            step=self.step(3),
            title=self.title,
            subtitle=self.subtitle,
            action_text=self.t("experience.add_action"),
            action_command=self.add_entry,
        )

        stack = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        stack.grid(row=1, column=0, sticky="nsew", padx=36, pady=(0, 28))
        stack.grid_columnconfigure(0, weight=1)
        stack.grid_rowconfigure(0, weight=1)
        self._build_list_view(stack)
        self._build_editor_view(stack)

    @property
    def ui_locale(self) -> str | None:
        return self.controller.settings.ui_locale if self.controller else None

    # --- list view -------------------------------------------------------

    def _build_list_view(self, stack) -> None:
        self.list_view = ctk.CTkFrame(stack, fg_color="transparent", corner_radius=0)
        self.list_view.grid(row=0, column=0, sticky="nsew")
        self.list_view.grid_columnconfigure(0, weight=1)
        self.list_view.grid_rowconfigure(0, weight=1)
        self.scroll = AutoHideScrollableFrame(
            self.list_view,
            width=600,
            height=420,
            corner_radius=0,
            fg_color="transparent",
            scrollbar_fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["muted"],
        )
        self.scroll.grid(row=0, column=0, sticky="nsew")
        self.scroll.grid_columnconfigure(0, weight=1)

    # --- editor view -----------------------------------------------------

    def _build_editor_view(self, stack) -> None:
        self.editor_view = ctk.CTkFrame(stack, fg_color="transparent", corner_radius=0)
        self.editor_view.grid(row=0, column=0, sticky="nsew")
        self.editor_view.grid_columnconfigure(0, weight=1)
        self.editor_view.grid_rowconfigure(0, weight=1)

        self.editor_scroll = AutoHideScrollableFrame(
            self.editor_view,
            width=600,
            height=400,
            corner_radius=0,
            fg_color="transparent",
            scrollbar_fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["muted"],
        )
        self.editor_scroll.grid(row=0, column=0, sticky="nsew")
        self.editor_scroll.grid_columnconfigure(0, weight=1)

        # Both forms share one cell, but the company form is a single field:
        # raising it would leave the taller position form showing underneath,
        # so only one of them is ever mapped.
        self.company_form = self._build_company_form(self.editor_scroll)
        self.position_form = self._build_position_form(self.editor_scroll)
        self.position_form.grid_remove()

        actions = ctk.CTkFrame(
            self.editor_view, fg_color=COLORS["background"], corner_radius=0
        )
        actions.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        self.save_button = button(
            actions,
            self.fonts,
            text=self.t("experience.save_entry"),
            command=self.save_entry,
            variant="primary",
            width=136,
        )
        self.save_button.pack(side="right")
        button(
            actions,
            self.fonts,
            text=self.t("action.cancel"),
            command=self.cancel_edit,
            variant="secondary",
            width=76,
        ).pack(side="right", padx=(0, 8))

    def _build_company_form(self, parent) -> ctk.CTkFrame:
        form = card(parent)
        form.grid(row=0, column=0, sticky="new", padx=(0, 8), pady=(0, 12))
        form.grid_columnconfigure(0, weight=1)
        self.company_entry = form_field(
            form,
            self.fonts,
            label=self.t("experience.company"),
            variable=self.company_var,
            placeholder=self.placeholders["company"],
            row=0,
            padx=22,
            pady=(22, 22),
        )
        return form

    def _build_position_form(self, parent) -> ctk.CTkFrame:
        form = card(parent)
        form.grid(row=0, column=0, sticky="new", padx=(0, 8), pady=(0, 12))
        form.grid_columnconfigure(0, weight=1)
        self.role_entry = form_field(
            form,
            self.fonts,
            label=self.t("experience.role"),
            variable=self.role_var,
            placeholder=self.placeholders["role"],
            row=0,
            padx=22,
            pady=(22, 12),
        )
        self.dates_field = DateRangeField(
            form,
            self.fonts,
            translate=self.t,
            ui_locale=self.ui_locale,
        )
        self.dates_field.grid(row=1, column=0, sticky="ew", padx=22, pady=(0, 14))
        form_field(
            form,
            self.fonts,
            label=self.t("experience.place"),
            variable=self.place_var,
            placeholder=self.placeholders["place"],
            row=2,
            padx=22,
            pady=(0, 12),
        )
        for row, (label_key, key, height, hint) in enumerate(TEXT_FIELDS, start=3):
            group = ctk.CTkFrame(form, fg_color="transparent")
            group.grid(
                row=row,
                column=0,
                sticky="ew",
                padx=22,
                pady=(0, 12 if row < 5 else 22),
            )
            group.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                group,
                text=self.t(label_key),
                font=self.fonts.label,
                text_color=COLORS["text"],
                anchor="w",
            ).grid(row=0, column=0, sticky="w")
            if hint:
                ctk.CTkLabel(
                    group,
                    text=self.t("experience.line_hint"),
                    font=self.fonts.small,
                    text_color=COLORS["muted"],
                    anchor="e",
                ).grid(row=0, column=1, sticky="e")
            widget = textbox(
                group,
                self.fonts,
                height=height,
                placeholder=self.placeholders[key],
            )
            widget.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0))
            self.editor_texts[key] = widget
        return form

    # --- state -----------------------------------------------------------

    @property
    def entries(self) -> list[dict[str, Any]]:
        return self.document["experience"]

    def positions(self, company: int) -> list[dict[str, Any]]:
        return self.entries[company]["positions"]

    def populate(self, data: dict[str, Any]) -> None:
        self.document = data
        self.refresh()
        self.show_list()

    def show_list(self) -> None:
        self.editor_open = False
        self.editing = None
        self.title.set(self.t("experience.title"))
        self.subtitle.set(self.t("experience.subtitle"))
        self.add_button.grid()
        self.list_view.tkraise()
        self.scroll._schedule_scrollbar_check()

    def _show_form(self, form) -> None:
        """Map exactly one of the two editor forms."""
        for candidate in (self.company_form, self.position_form):
            if candidate is form:
                candidate.grid()
            else:
                candidate.grid_remove()

    def _show_editor(self, *, title_key: str, subtitle_key: str, save_key: str) -> None:
        self.editor_open = True
        self.title.set(self.t(title_key))
        self.subtitle.set(self.t(subtitle_key))
        self.save_button.configure(text=self.t(save_key))
        self.add_button.grid_remove()
        self.editor_view.tkraise()
        self.editor_scroll._schedule_scrollbar_check()

    def selected_index(self) -> int | None:
        return self.selection

    # --- list rendering --------------------------------------------------

    def refresh(self, selection: int | None = None) -> None:
        self.selection = selection
        for child in self.scroll.winfo_children():
            child.destroy()
        self.scroll.grid_columnconfigure(0, weight=1)

        if not self.entries:
            self._render_empty_state()
            return

        commands = {
            "edit_company": self.edit_entry,
            "move_company": self.move_entry,
            "delete_company": self.delete_entry,
            "add_position": self.add_position,
            "edit_position": self.edit_position,
            "move_position": self.move_position,
            "delete_position": self.delete_position,
        }
        for index, entry in enumerate(self.entries):
            render_company_card(
                self.scroll,
                self.fonts,
                index=index,
                entry=entry,
                translate=self.t,
                ui_locale=self.ui_locale,
                commands=commands,
            )
        self.scroll._schedule_scrollbar_check()

    def _render_empty_state(self) -> None:
        empty = card(self.scroll)
        empty.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        empty.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            empty,
            text=self.t("experience.empty_title"),
            font=self.fonts.card_title,
            text_color=COLORS["text"],
        ).grid(row=0, column=0, pady=(28, 4))
        ctk.CTkLabel(
            empty,
            text=self.t("experience.empty_subtitle"),
            font=self.fonts.small,
            text_color=COLORS["muted"],
        ).grid(row=1, column=0)
        button(
            empty,
            self.fonts,
            text=self.t("experience.empty_action"),
            command=self.add_entry,
            variant="primary",
            width=190,
        ).grid(row=2, column=0, pady=(16, 28))
        self.scroll._schedule_scrollbar_check()

    # --- company commands ------------------------------------------------

    def _open_company_editor(self, company: int | None, *, is_new: bool) -> None:
        self.editing = (company, None)
        self._show_form(self.company_form)
        self._show_editor(
            title_key="experience.add_title" if is_new else "experience.edit_title",
            subtitle_key="experience.edit_subtitle",
            save_key="experience.save_entry",
        )
        self.after_idle(self.company_entry.focus_set)

    def add_entry(self) -> None:
        self.selection = None
        self.company_var.set("")
        self._open_company_editor(None, is_new=True)

    def edit_entry(self, index: int | None = None) -> None:
        index = self._require_company(index)
        if index is None:
            return
        self.selection = index
        self.company_var.set(self.entries[index].get("company", ""))
        self._open_company_editor(index, is_new=False)

    def delete_entry(self, index: int | None = None) -> None:
        index = self._require_company(index, quiet=True)
        if index is None:
            return
        if messagebox.askyesno(
            self.t("dialog.delete_entry.title"),
            self.t("dialog.delete_entry.message"),
            parent=self,
        ):
            del self.entries[index]
            self.refresh(min(index, len(self.entries) - 1) if self.entries else None)
            self.on_change()

    def move_entry(self, direction: int, index: int | None = None) -> None:
        index = self._require_company(index, quiet=True)
        target = index + direction if index is not None else -1
        if index is None or target < 0 or target >= len(self.entries):
            return
        entries = self.entries
        entries[index], entries[target] = entries[target], entries[index]
        self.refresh(target)
        self.on_change()

    def _require_company(self, index: int | None, *, quiet: bool = False) -> int | None:
        if index is None:
            index = self.selected_index()
        if index is None or not 0 <= index < len(self.entries):
            if not quiet:
                messagebox.showinfo(
                    self.t("dialog.select_entry.title"),
                    self.t("dialog.select_entry.message"),
                    parent=self,
                )
            return None
        return index

    # --- position commands -----------------------------------------------

    def _load_position(self, position: dict[str, Any]) -> None:
        self.role_var.set(position.get("role", ""))
        self.place_var.set(position.get("place", ""))
        self.dates_field.set_value(
            position.get("start", ""),
            position.get("end", ""),
            bool(position.get("current")),
        )
        values = {
            "intro": position.get("intro", ""),
            "work": "\n".join(position.get("work", [])),
            "results": "\n".join(position.get("results", [])),
        }
        for key, widget in self.editor_texts.items():
            widget.set_value(values[key])

    def _open_position_editor(
        self, company: int, position: int | None, *, is_new: bool
    ) -> None:
        self.editing = (company, position if position is not None else -1)
        self._show_form(self.position_form)
        self._show_editor(
            title_key=(
                "experience.position_add_title"
                if is_new
                else "experience.position_edit_title"
            ),
            subtitle_key="experience.position_subtitle",
            save_key="experience.save_position",
        )
        self.after_idle(self.role_entry.focus_set)

    def add_position(self, company: int) -> None:
        if not 0 <= company < len(self.entries):
            return
        self.selection = company
        self._load_position(empty_position())
        self._open_position_editor(company, None, is_new=True)

    def edit_position(self, company: int, index: int) -> None:
        if not 0 <= company < len(self.entries):
            return
        positions = self.positions(company)
        if not 0 <= index < len(positions):
            return
        self.selection = company
        self._load_position(deepcopy(positions[index]))
        self._open_position_editor(company, index, is_new=False)

    def delete_position(self, company: int, index: int) -> None:
        if not 0 <= company < len(self.entries):
            return
        positions = self.positions(company)
        if not 0 <= index < len(positions):
            return
        if not messagebox.askyesno(
            self.t("dialog.delete_position.title"),
            self.t("dialog.delete_position.message"),
            parent=self,
        ):
            return
        del positions[index]
        self.refresh(company)
        self.on_change()

    def move_position(self, direction: int, company: int, index: int) -> None:
        if not 0 <= company < len(self.entries):
            return
        positions = self.positions(company)
        target = index + direction
        if not 0 <= index < len(positions) or not 0 <= target < len(positions):
            return
        positions[index], positions[target] = positions[target], positions[index]
        self.refresh(company)
        self.on_change()

    # --- saving ----------------------------------------------------------

    def cancel_edit(self) -> None:
        self.show_list()

    def save_entry(self) -> None:
        if self.editing is None:
            return
        company, position = self.editing
        if position is None:
            self._save_company(company)
        else:
            self._save_position(company, None if position < 0 else position)

    def _save_company(self, company: int | None) -> None:
        name = self.company_var.get().strip()
        if not name:
            messagebox.showwarning(
                self.t("dialog.missing_info.title"),
                self.t("dialog.missing_info.message"),
                parent=self,
            )
            return
        if company is None:
            entry = empty_experience()
            entry["company"] = name
            self.entries.append(entry)
            selection = len(self.entries) - 1
        else:
            self.entries[company]["company"] = name
            selection = company
        self.refresh(selection)
        self.show_list()
        self.on_change()
        if company is None:
            # A company without a role says nothing, so go straight on to one.
            self.add_position(selection)

    def _save_position(self, company: int, index: int | None) -> None:
        role = self.role_var.get().strip()
        start = self.dates_field.start
        if not role or not start:
            messagebox.showwarning(
                self.t("dialog.missing_info.title"),
                self.t("dialog.missing_position.message"),
                parent=self,
            )
            return
        end = self.dates_field.end
        if end and parse_ym(end) < parse_ym(start):
            messagebox.showwarning(
                self.t("dialog.invalid_dates.title"),
                self.t("dialog.invalid_dates.message"),
                parent=self,
            )
            return
        position = empty_position()
        position.update(
            {
                "role": role,
                "start": start,
                "end": end,
                "current": self.dates_field.is_current,
                "place": self.place_var.get().strip(),
                "intro": self.editor_texts["intro"].get("1.0", "end").strip(),
                "work": split_lines(self.editor_texts["work"].get("1.0", "end")),
                "results": split_lines(self.editor_texts["results"].get("1.0", "end")),
            }
        )
        positions = self.positions(company)
        if index is None:
            positions.append(position)
        else:
            positions[index] = position
        self.refresh(company)
        self.show_list()
        self.on_change()
