"""Section 3 — experience list with an inline entry editor."""
from __future__ import annotations

import tkinter as tk
from copy import deepcopy
from tkinter import messagebox
from typing import Any

import customtkinter as ctk

from cv_builder.domain.model import empty_experience
from cv_builder.domain.text import split_lines
from cv_builder.ui.components.fields import card, form_field, section_header, textbox
from cv_builder.ui.components.scrollable import AutoHideScrollableFrame
from cv_builder.ui.placeholders import PLACEHOLDERS
from cv_builder.ui.screens.sections.base import Section
from cv_builder.ui.theme import COLORS, button


ENTRY_FIELDS = ("company", "duration", "role", "dates", "place")
TEXT_FIELDS = (
    ("Role or project description", "intro", 72, None),
    ("Key responsibilities", "work", 94, "One item per line"),
    ("Results", "results", 86, "One item per line"),
)


class ExperienceSection(Section):
    def build(self) -> None:
        self.document: dict[str, Any] = {"experience": []}
        self.editor_vars: dict[str, tk.StringVar] = {}
        self.editor_texts: dict[str, Any] = {}
        self.editing_index: int | None = None
        self.selection: int | None = None
        self.editor_open = False
        self.title = tk.StringVar(value="Experience")
        self.subtitle = tk.StringVar(value="Put the most relevant role first.")

        self.grid_rowconfigure(1, weight=1)
        self.add_button = section_header(
            self,
            self.fonts,
            step="Section 3 of 5",
            title=self.title,
            subtitle=self.subtitle,
            action_text="+  Add role",
            action_command=self.add_entry,
        )

        stack = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        stack.grid(row=1, column=0, sticky="nsew", padx=36, pady=(0, 28))
        stack.grid_columnconfigure(0, weight=1)
        stack.grid_rowconfigure(0, weight=1)
        self._build_list_view(stack)
        self._build_editor_view(stack)

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

        form = card(self.editor_scroll)
        form.grid(row=0, column=0, sticky="new", padx=(0, 8), pady=(0, 12))
        form.grid_columnconfigure((0, 1), weight=1, uniform="experience")

        for key in ENTRY_FIELDS:
            self.editor_vars[key] = tk.StringVar()

        self.company_entry = form_field(
            form,
            self.fonts,
            label="Company",
            variable=self.editor_vars["company"],
            placeholder=PLACEHOLDERS["company"],
            row=0,
            columnspan=2,
            padx=22,
            pady=(22, 12),
        )
        form_field(
            form,
            self.fonts,
            label="Role",
            variable=self.editor_vars["role"],
            placeholder=PLACEHOLDERS["role"],
            row=1,
            columnspan=2,
            padx=22,
            pady=(0, 12),
        )
        form_field(
            form,
            self.fonts,
            label="Dates",
            variable=self.editor_vars["dates"],
            placeholder=PLACEHOLDERS["dates"],
            row=2,
            column=0,
            padx=(22, 7),
            pady=(0, 12),
        )
        form_field(
            form,
            self.fonts,
            label="Total duration",
            variable=self.editor_vars["duration"],
            placeholder=PLACEHOLDERS["duration"],
            row=2,
            column=1,
            padx=(7, 22),
            pady=(0, 12),
        )
        form_field(
            form,
            self.fonts,
            label="Location",
            variable=self.editor_vars["place"],
            placeholder=PLACEHOLDERS["place"],
            row=3,
            columnspan=2,
            padx=22,
            pady=(0, 12),
        )

        for row, (label, key, height, hint) in enumerate(TEXT_FIELDS, start=4):
            group = ctk.CTkFrame(form, fg_color="transparent")
            group.grid(
                row=row,
                column=0,
                columnspan=2,
                sticky="ew",
                padx=22,
                pady=(0, 12 if row < 6 else 22),
            )
            group.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                group,
                text=label,
                font=self.fonts.label,
                text_color=COLORS["text"],
                anchor="w",
            ).grid(row=0, column=0, sticky="w")
            if hint:
                ctk.CTkLabel(
                    group,
                    text=hint,
                    font=self.fonts.small,
                    text_color=COLORS["muted"],
                    anchor="e",
                ).grid(row=0, column=1, sticky="e")
            widget = textbox(
                group,
                self.fonts,
                height=height,
                placeholder=PLACEHOLDERS[key],
            )
            widget.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0))
            self.editor_texts[key] = widget

        actions = ctk.CTkFrame(
            self.editor_view, fg_color=COLORS["background"], corner_radius=0
        )
        actions.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        button(
            actions,
            self.fonts,
            text="Save entry",
            command=self.save_entry,
            variant="primary",
            width=106,
        ).pack(side="right")
        button(
            actions,
            self.fonts,
            text="Cancel",
            command=self.cancel_edit,
            variant="secondary",
            width=76,
        ).pack(side="right", padx=(0, 8))

    # --- state -----------------------------------------------------------

    @property
    def entries(self) -> list[dict[str, Any]]:
        return self.document["experience"]

    def populate(self, data: dict[str, Any]) -> None:
        self.document = data
        self.refresh()
        self.show_list()

    def show_list(self) -> None:
        self.editor_open = False
        self.title.set("Experience")
        self.subtitle.set("Put the most relevant role first.")
        self.add_button.grid()
        self.list_view.tkraise()
        self.scroll._schedule_scrollbar_check()

    def _show_editor(self, *, is_new: bool) -> None:
        self.editor_open = True
        self.title.set("Add experience" if is_new else "Edit experience")
        self.subtitle.set(
            "Describe the role, responsibilities and measurable results."
        )
        self.add_button.grid_remove()
        self.editor_view.tkraise()
        self.editor_scroll._schedule_scrollbar_check()
        self.after_idle(self.company_entry.focus_set)

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

        for index, item in enumerate(self.entries):
            self._render_entry_card(index, item)
        self.scroll._schedule_scrollbar_check()

    def _render_empty_state(self) -> None:
        empty = card(self.scroll)
        empty.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        empty.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            empty,
            text="No experience added yet",
            font=self.fonts.card_title,
            text_color=COLORS["text"],
        ).grid(row=0, column=0, pady=(28, 4))
        ctk.CTkLabel(
            empty,
            text="Add a role to show your responsibilities and impact.",
            font=self.fonts.small,
            text_color=COLORS["muted"],
        ).grid(row=1, column=0)
        button(
            empty,
            self.fonts,
            text="+  Add your first role",
            command=self.add_entry,
            variant="primary",
            width=154,
        ).grid(row=2, column=0, pady=(16, 28))
        self.scroll._schedule_scrollbar_check()

    def _render_entry_card(self, index: int, item: dict[str, Any]) -> None:
        entry_card = card(self.scroll)
        entry_card.grid(row=index, column=0, sticky="ew", padx=(0, 8), pady=(0, 10))
        entry_card.grid_columnconfigure(0, weight=1)
        content = ctk.CTkFrame(entry_card, fg_color="transparent")
        content.grid(row=0, column=0, sticky="ew", padx=18, pady=16)
        content.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            content,
            text=item.get("role") or "Untitled role",
            font=self.fonts.card_title,
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            content,
            text=item.get("company") or "Company not specified",
            font=self.fonts.body,
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(3, 0))
        meta = "  ·  ".join(
            value
            for value in (item.get("dates", ""), item.get("place", ""))
            if value
        )
        if meta:
            ctk.CTkLabel(
                content,
                text=meta,
                font=self.fonts.small,
                text_color=COLORS["muted"],
                anchor="w",
            ).grid(row=2, column=0, sticky="w", pady=(4, 0))

        actions = ctk.CTkFrame(entry_card, fg_color="transparent")
        actions.grid(row=0, column=1, sticky="e", padx=(8, 14))
        button(
            actions,
            self.fonts,
            text="Edit",
            command=lambda value=index: self.edit_entry(value),
            variant="secondary",
            width=56,
            height=34,
        ).pack(side="left", padx=(0, 4))
        button(
            actions,
            self.fonts,
            text="↑",
            command=lambda value=index: self.move_entry(-1, value),
            variant="ghost",
            width=34,
            height=34,
        ).pack(side="left")
        button(
            actions,
            self.fonts,
            text="↓",
            command=lambda value=index: self.move_entry(1, value),
            variant="ghost",
            width=34,
            height=34,
        ).pack(side="left")
        button(
            actions,
            self.fonts,
            text="Delete",
            command=lambda value=index: self.delete_entry(value),
            variant="danger",
            width=60,
            height=34,
        ).pack(side="left", padx=(3, 0))

    # --- commands --------------------------------------------------------

    def _load_editor(self, item: dict[str, Any]) -> None:
        for key, variable in self.editor_vars.items():
            variable.set(item.get(key, ""))
        values = {
            "intro": item.get("intro", ""),
            "work": "\n".join(item.get("work", [])),
            "results": "\n".join(item.get("results", [])),
        }
        for key, widget in self.editor_texts.items():
            widget.set_value(values[key])

    def add_entry(self) -> None:
        self.editing_index = None
        self.selection = None
        self._load_editor(empty_experience())
        self._show_editor(is_new=True)

    def edit_entry(self, index: int | None = None) -> None:
        if index is None:
            index = self.selected_index()
        if index is None or not 0 <= index < len(self.entries):
            messagebox.showinfo(
                "Select an entry",
                "Select an experience entry first.",
                parent=self,
            )
            return
        self.editing_index = index
        self.selection = index
        self._load_editor(deepcopy(self.entries[index]))
        self._show_editor(is_new=False)

    def cancel_edit(self) -> None:
        self.editing_index = None
        self.show_list()

    def save_entry(self) -> None:
        item = {key: variable.get().strip() for key, variable in self.editor_vars.items()}
        if not item["company"] or not item["role"]:
            messagebox.showwarning(
                "Missing information",
                "Company and role are required.",
                parent=self,
            )
            return
        item.update(
            {
                "intro": self.editor_texts["intro"].get("1.0", "end").strip(),
                "work": split_lines(self.editor_texts["work"].get("1.0", "end")),
                "results": split_lines(self.editor_texts["results"].get("1.0", "end")),
            }
        )
        if self.editing_index is None:
            self.entries.append(item)
            selection = len(self.entries) - 1
        else:
            self.entries[self.editing_index] = item
            selection = self.editing_index
        self.editing_index = None
        self.refresh(selection)
        self.show_list()
        self.on_change()

    def delete_entry(self, index: int | None = None) -> None:
        if index is None:
            index = self.selected_index()
        if index is None or not 0 <= index < len(self.entries):
            return
        if messagebox.askyesno(
            "Delete entry",
            "Delete this experience entry?",
            parent=self,
        ):
            del self.entries[index]
            self.refresh(
                min(index, len(self.entries) - 1) if self.entries else None
            )
            self.on_change()

    def move_entry(self, direction: int, index: int | None = None) -> None:
        if index is None:
            index = self.selected_index()
        target = index + direction if index is not None else -1
        if index is None or target < 0 or target >= len(self.entries):
            return
        entries = self.entries
        entries[index], entries[target] = entries[target], entries[index]
        self.refresh(target)
        self.on_change()
