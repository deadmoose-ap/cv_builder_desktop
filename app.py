"""Cross-platform desktop interface for CV Builder."""
from __future__ import annotations

import json
import sys
import tkinter as tk
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from cv_library import CVLibrary
from cv_model import example_document, new_document, save_document
from pdf_generator import generate_pdf


APP_NAME = "CV Builder"
SECTION_ORDER = ("profile", "summary", "experience", "education")
COLORS = {
    "background": "#F6F7FB",
    "surface": "#FFFFFF",
    "surface_alt": "#EFF3F8",
    "text": "#172033",
    "muted": "#667085",
    "border": "#D7DDE8",
    "accent": "#2F6BFF",
    "accent_hover": "#2457D6",
    "selection": "#EAF0FF",
    "danger": "#B42318",
    "danger_hover": "#FDECEC",
    "success": "#127A45",
}
PLACEHOLDERS = {
    "name": "YOUR NAME",
    "headline": "YOUR JOB TITLE | YOUR SPECIALIZATION | YOUR KEY VALUE",
    "location": "YOUR CITY, YOUR COUNTRY",
    "email": "your.email@example.com",
    "linkedin": "linkedin.com/in/your-profile",
    "skills": "SKILL ONE\nSKILL TWO\nSKILL THREE",
    "summary": (
        "Write a short introduction about your professional background and main "
        "expertise.\n\nDescribe the teams, projects, or products you have worked "
        "with.\n\nHighlight your most relevant results and areas of specialization."
    ),
    "company": "CURRENT OR MOST RECENT COMPANY",
    "duration": "X YEARS X MONTHS",
    "role": "YOUR JOB TITLE",
    "dates": "MONTH YEAR - PRESENT",
    "place": "CITY, COUNTRY",
    "intro": "Add a one-sentence role or project description.",
    "work": "Describe a key responsibility.\nDescribe another contribution.",
    "results": "Describe a measurable result or business impact.",
    "institution": "UNIVERSITY OR SCHOOL NAME",
    "qualification": "DEGREE OR QUALIFICATION (YEAR - YEAR)",
}

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


def split_paragraphs(value: str) -> list[str]:
    return [part.strip() for part in value.split("\n\n") if part.strip()]


def split_lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def calculate_completion(data: dict) -> int:
    """Return a simple, explainable completion percentage for the current CV."""
    profile = data.get("profile", {})
    education = data.get("education", {})
    checks = (
        bool(profile.get("name")),
        bool(profile.get("headline")),
        bool(profile.get("location")),
        bool(profile.get("email")),
        bool(profile.get("linkedin")),
        bool(profile.get("skills")),
        bool(profile.get("summary")),
        bool(data.get("experience")),
        bool(education.get("institution")),
        bool(education.get("qualification")),
    )
    return round(sum(bool(value) for value in checks) / len(checks) * 100)


def empty_experience() -> dict:
    return {
        "company": "",
        "duration": "",
        "role": "",
        "dates": "",
        "place": "",
        "intro": "",
        "work": [],
        "results": [],
    }


class AutoHideScrollableFrame(ctk.CTkScrollableFrame):
    """CustomTkinter scroll frame that hides its bar when content fits."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._visibility_job: str | None = None
        self.bind("<Configure>", self._schedule_scrollbar_check, add="+")
        self._parent_canvas.bind(
            "<Configure>", self._schedule_scrollbar_check, add="+"
        )
        self.after_idle(self._update_scrollbar_visibility)

    def _schedule_scrollbar_check(self, _event=None):
        if self._visibility_job:
            self.after_cancel(self._visibility_job)
        self._visibility_job = self.after(40, self._update_scrollbar_visibility)

    def _update_scrollbar_visibility(self):
        self._visibility_job = None
        if not self.winfo_exists() or not self._parent_canvas.winfo_exists():
            return
        bbox = self._parent_canvas.bbox(self._create_window_id)
        content_height = (bbox[3] - bbox[1]) if bbox else 0
        available_height = self._parent_canvas.winfo_height()
        needs_scrollbar = content_height > available_height + 2
        if needs_scrollbar:
            if not self._scrollbar.winfo_ismapped():
                self._scrollbar.grid()
        elif self._scrollbar.winfo_ismapped():
            self._scrollbar.grid_remove()


class PlaceholderEntry(ctk.CTkEntry):
    """CTkEntry placeholder overlay that never mutates its StringVar."""

    def __init__(self, *args, placeholder_text: str = "", **kwargs):
        self.placeholder_text = placeholder_text
        self._placeholder_variable = kwargs.get("textvariable")
        self._has_focus = False
        kwargs.pop("placeholder_text_color", None)
        super().__init__(*args, **kwargs)
        self._placeholder_label = ctk.CTkLabel(
            self,
            text=placeholder_text,
            font=kwargs.get("font"),
            text_color=COLORS["muted"],
            fg_color="transparent",
            anchor="w",
            height=20,
        )
        self._placeholder_label.place(x=12, rely=0.5, anchor="w")
        self._placeholder_label.bind(
            "<Button-1>", self._focus_from_placeholder, add="+"
        )
        self.bind("<FocusIn>", self._handle_focus_in, add="+")
        self.bind("<FocusOut>", self._handle_focus_out, add="+")
        if self._placeholder_variable is not None:
            self._placeholder_variable.trace_add("write", self._sync_placeholder)
        self.after_idle(self._sync_placeholder)

    def _focus_from_placeholder(self, _event=None):
        self._has_focus = True
        self._placeholder_label.place_forget()
        self._entry.focus_set()

    def _handle_focus_in(self, _event=None):
        self._has_focus = True
        self._placeholder_label.place_forget()

    def _handle_focus_out(self, _event=None):
        self._has_focus = False
        self._sync_placeholder()

    def _sync_placeholder(self, *_args):
        if not hasattr(self, "_placeholder_label"):
            return
        value = (
            self._placeholder_variable.get()
            if self._placeholder_variable is not None
            else self.get()
        )
        if self.placeholder_text and not self._has_focus and not value:
            self._placeholder_label.place(x=12, rely=0.5, anchor="w")
            self._placeholder_label.lift()
        else:
            self._placeholder_label.place_forget()


class PlaceholderTextbox(ctk.CTkTextbox):
    """CTkTextbox with non-data placeholder text."""

    def __init__(self, *args, placeholder_text: str = "", **kwargs):
        self.placeholder_text = placeholder_text
        self._placeholder_active = False
        self._value_text_color = kwargs.get("text_color", COLORS["text"])
        super().__init__(*args, **kwargs)
        self.bind("<FocusIn>", self._handle_placeholder_focus_in, add="+")
        self.bind("<FocusOut>", self._handle_placeholder_focus_out, add="+")
        self.after_idle(self._show_placeholder_if_empty)

    def _raw_value(self) -> str:
        return super().get("1.0", "end-1c")

    def _show_placeholder_if_empty(self, _event=None) -> None:
        if self.placeholder_text and not self._raw_value().strip():
            super().delete("1.0", "end")
            super().insert("1.0", self.placeholder_text)
            self.configure(text_color=COLORS["muted"])
            self._placeholder_active = True

    def _handle_placeholder_focus_in(self, _event=None) -> None:
        if self._placeholder_active:
            super().delete("1.0", "end")
            self.configure(text_color=self._value_text_color)
            self._placeholder_active = False

    def _handle_placeholder_focus_out(self, _event=None) -> None:
        self._show_placeholder_if_empty()

    def get(self, index1: str, index2: str | None = None) -> str:
        if self._placeholder_active:
            return ""
        return super().get(index1, index2)

    def set_value(self, value: str) -> None:
        self._placeholder_active = False
        self.configure(text_color=self._value_text_color)
        super().delete("1.0", "end")
        if value:
            super().insert("1.0", value)
        else:
            self._show_placeholder_if_empty()


class CVBuilderApp(ctk.CTk):
    def __init__(
        self,
        library: CVLibrary | None = None,
        *,
        show_library_on_start: bool = True,
    ):
        super().__init__(fg_color=COLORS["background"])
        self.title(APP_NAME)
        self.geometry("1120x780")
        self.minsize(940, 680)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.library = library or CVLibrary()
        self.data = new_document()
        self.current_document_id: str | None = None
        self.current_document_title = ""
        self.profile_vars: dict[str, tk.StringVar] = {}
        self.profile_entries: dict[str, PlaceholderEntry] = {}
        self.education_vars: dict[str, tk.StringVar] = {}
        self.editor_vars: dict[str, tk.StringVar] = {}
        self.section_frames: dict[str, ctk.CTkFrame] = {}
        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        self.current_section = "profile"
        self.editing_experience_index: int | None = None
        self.experience_selection: int | None = None
        self.experience_editor_open = False
        self._loading = True
        self._progress_job: str | None = None
        self._autosave_job: str | None = None

        self.status = tk.StringVar(value="Local CV library")
        self.progress_text = tk.StringVar(value="0% complete")
        self.summary_count = tk.StringVar(value="0 characters")
        self.experience_title = tk.StringVar(value="Experience")
        self.experience_subtitle = tk.StringVar(
            value="Put the most relevant role first."
        )

        self._configure_fonts()
        self.editor_view = ctk.CTkFrame(
            self, corner_radius=0, fg_color=COLORS["background"]
        )
        self.library_view = ctk.CTkFrame(
            self, corner_radius=0, fg_color=COLORS["background"]
        )
        for view in (self.editor_view, self.library_view):
            view.grid(row=0, column=0, sticky="nsew")
            view.grid_columnconfigure(0, weight=1)
            view.grid_rowconfigure(0, weight=1)
        self._build_shell()
        self._build_sections()
        self._build_library_screen()
        self.populate_form()
        self.show_section("profile")
        self._bind_shortcuts()
        self.protocol("WM_DELETE_WINDOW", self._close_application)
        self._loading = False
        self._update_progress()
        if show_library_on_start:
            self.show_library()
        else:
            self.editor_view.tkraise()

    def _configure_fonts(self):
        self.font_brand = ctk.CTkFont(size=17, weight="bold")
        self.font_body = ctk.CTkFont(size=13)
        self.font_button = ctk.CTkFont(size=13, weight="normal")
        self.font_button_bold = ctk.CTkFont(size=13, weight="bold")
        self.font_small = ctk.CTkFont(size=12)
        self.font_small_bold = ctk.CTkFont(size=11, weight="bold")
        self.font_label = ctk.CTkFont(size=13, weight="bold")
        self.font_card_title = ctk.CTkFont(size=15, weight="bold")
        self.font_page_title = ctk.CTkFont(size=26, weight="bold")
        self.font_nav = ctk.CTkFont(size=14)
        self.font_nav_active = ctk.CTkFont(size=14, weight="bold")

    def _button(
        self,
        parent,
        *,
        text: str,
        command,
        variant: str = "secondary",
        width: int = 84,
        height: int = 38,
        anchor: str = "center",
    ) -> ctk.CTkButton:
        common = {
            "text": text,
            "command": command,
            "width": width,
            "height": height,
            "corner_radius": 8,
            "font": self.font_button,
            "anchor": anchor,
            "border_spacing": 5,
        }
        variants = {
            "primary": {
                "fg_color": COLORS["accent"],
                "hover_color": COLORS["accent_hover"],
                "text_color": "#FFFFFF",
                "font": self.font_button_bold,
            },
            "secondary": {
                "fg_color": COLORS["surface"],
                "hover_color": COLORS["selection"],
                "text_color": COLORS["text"],
                "border_width": 1,
                "border_color": COLORS["border"],
            },
            "ghost": {
                "fg_color": "transparent",
                "hover_color": COLORS["surface_alt"],
                "text_color": COLORS["muted"],
            },
            "danger": {
                "fg_color": "transparent",
                "hover_color": COLORS["danger_hover"],
                "text_color": COLORS["danger"],
            },
        }
        common.update(variants[variant])
        return ctk.CTkButton(parent, **common)

    def _build_shell(self):
        parent = self.editor_view
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=0)
        parent.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(
            parent,
            height=64,
            corner_radius=0,
            fg_color=COLORS["surface"],
        )
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            header,
            text=APP_NAME,
            font=self.font_brand,
            text_color=COLORS["text"],
        ).grid(row=0, column=0, sticky="w", padx=(20, 0), pady=12)
        ctk.CTkLabel(
            header,
            textvariable=self.status,
            font=self.font_small,
            text_color=COLORS["muted"],
        ).grid(row=0, column=1, sticky="w", padx=(18, 10))

        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.grid(row=0, column=2, sticky="e", padx=(0, 18), pady=11)
        self._button(
            actions,
            text="All CVs",
            command=self.show_library,
            variant="ghost",
            width=70,
        ).pack(side="left", padx=(0, 5))
        self._button(
            actions,
            text="Export JSON",
            command=self.export_current_json,
            variant="secondary",
            width=96,
        ).pack(side="left", padx=(0, 8))
        self._button(
            actions,
            text="Export PDF",
            command=self.generate,
            variant="primary",
            width=112,
        ).pack(side="left")

        workspace = ctk.CTkFrame(
            parent, corner_radius=0, fg_color=COLORS["background"]
        )
        workspace.grid(row=1, column=0, sticky="nsew")
        workspace.grid_columnconfigure(1, weight=1)
        workspace.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(
            workspace,
            width=218,
            corner_radius=0,
            fg_color=COLORS["surface_alt"],
        )
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)
        sidebar.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(
            sidebar,
            text="BUILD YOUR CV",
            font=self.font_small_bold,
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=22, pady=(28, 0))
        ctk.CTkLabel(
            sidebar,
            textvariable=self.progress_text,
            font=self.font_body,
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=22, pady=(9, 8))
        self.progress_bar = ctk.CTkProgressBar(
            sidebar,
            height=6,
            corner_radius=3,
            fg_color=COLORS["border"],
            progress_color=COLORS["border"],
        )
        self.progress_bar.grid(row=2, column=0, sticky="ew", padx=22)
        self.progress_bar.set(0)

        navigation = ctk.CTkFrame(sidebar, fg_color="transparent")
        navigation.grid(row=3, column=0, sticky="new", padx=14, pady=(24, 0))
        navigation.grid_columnconfigure(0, weight=1)
        labels = {
            "profile": "1    Profile",
            "summary": "2    Summary",
            "experience": "3    Experience",
            "education": "4    Education",
        }
        for row, section in enumerate(SECTION_ORDER):
            button = ctk.CTkButton(
                navigation,
                text=labels[section],
                command=lambda value=section: self.show_section(value),
                height=44,
                corner_radius=9,
                fg_color="transparent",
                hover_color=COLORS["surface"],
                text_color=COLORS["muted"],
                font=self.font_nav,
                anchor="w",
                border_spacing=12,
            )
            button.grid(row=row, column=0, sticky="ew", pady=2)
            self.nav_buttons[section] = button

        ctk.CTkLabel(
            sidebar,
            text="Local and private\nYour data stays on this device.",
            font=self.font_small,
            text_color=COLORS["muted"],
            justify="left",
            anchor="sw",
            wraplength=174,
        ).grid(row=5, column=0, sticky="sw", padx=22, pady=(0, 24))

        self.content_host = ctk.CTkFrame(
            workspace, corner_radius=0, fg_color=COLORS["background"]
        )
        self.content_host.grid(row=0, column=1, sticky="nsew")
        self.content_host.grid_columnconfigure(0, weight=1)
        self.content_host.grid_rowconfigure(0, weight=1)

    def _build_library_screen(self):
        parent = self.library_view
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=0)
        parent.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(
            parent,
            height=64,
            corner_radius=0,
            fg_color=COLORS["surface"],
        )
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            header,
            text=APP_NAME,
            font=self.font_brand,
            text_color=COLORS["text"],
        ).grid(row=0, column=0, sticky="w", padx=(20, 0), pady=12)
        ctk.CTkLabel(
            header,
            text="Your CV library",
            font=self.font_small,
            text_color=COLORS["muted"],
        ).grid(row=0, column=1, sticky="w", padx=(18, 10))

        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.grid(row=0, column=2, sticky="e", padx=(0, 18), pady=11)
        self._button(
            actions,
            text="Example JSON",
            command=self.export_example_json,
            variant="ghost",
            width=104,
        ).pack(side="left", padx=(0, 4))
        self._button(
            actions,
            text="Import JSON",
            command=self.import_json,
            variant="secondary",
            width=96,
        ).pack(side="left", padx=(0, 8))
        self._button(
            actions,
            text="+  New CV",
            command=self.create_cv,
            variant="primary",
            width=96,
        ).pack(side="left")

        content = ctk.CTkFrame(
            parent, corner_radius=0, fg_color=COLORS["background"]
        )
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(
            content,
            text="YOUR DOCUMENTS",
            font=self.font_small_bold,
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=44, pady=(34, 0))
        ctk.CTkLabel(
            content,
            text="Choose a CV to continue",
            font=self.font_page_title,
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=44, pady=(5, 20))

        self.library_scroll = AutoHideScrollableFrame(
            content,
            corner_radius=0,
            fg_color="transparent",
            scrollbar_fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["muted"],
        )
        self.library_scroll.grid(
            row=2, column=0, sticky="nsew", padx=36, pady=(0, 32)
        )
        self.library_scroll.grid_columnconfigure(0, weight=1)

    def _format_modified_date(self, value: str) -> str:
        try:
            timestamp = datetime.fromisoformat(value)
            return timestamp.astimezone().strftime("%d %b %Y, %H:%M")
        except (TypeError, ValueError):
            return "Recently updated"

    def refresh_library(self):
        for child in self.library_scroll.winfo_children():
            child.destroy()
        self.library_scroll.grid_columnconfigure(0, weight=1)

        try:
            records = self.library.list_documents()
        except Exception as error:
            records = []
            messagebox.showerror("Could not open CV library", str(error), parent=self)

        if not records:
            empty = self._card(self.library_scroll)
            empty.grid(row=0, column=0, sticky="ew", padx=(8, 16))
            empty.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                empty,
                text="Create your first CV",
                font=self.font_card_title,
                text_color=COLORS["text"],
            ).grid(row=0, column=0, pady=(34, 5))
            ctk.CTkLabel(
                empty,
                text="Your changes will be saved automatically on this device.",
                font=self.font_body,
                text_color=COLORS["muted"],
            ).grid(row=1, column=0)
            self._button(
                empty,
                text="+  Create CV",
                command=self.create_cv,
                variant="primary",
                width=112,
            ).grid(row=2, column=0, pady=(18, 34))
            self.library_scroll._schedule_scrollbar_check()
            return

        for row, record in enumerate(records):
            try:
                document = self.library.load_document(record.id)
                person = document["profile"].get("name") or "No name added yet"
                completion = calculate_completion(document)
            except Exception:
                person = "Document could not be previewed"
                completion = 0

            card = self._card(self.library_scroll)
            card.grid(
                row=row,
                column=0,
                sticky="ew",
                padx=(8, 16),
                pady=(0, 10),
            )
            card.grid_columnconfigure(0, weight=1)
            details = ctk.CTkFrame(card, fg_color="transparent")
            details.grid(row=0, column=0, sticky="ew", padx=20, pady=17)
            details.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                details,
                text=record.title,
                font=self.font_card_title,
                text_color=COLORS["text"],
                anchor="w",
            ).grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(
                details,
                text=f"{person}  ·  {completion}% complete",
                font=self.font_body,
                text_color=COLORS["muted"],
                anchor="w",
            ).grid(row=1, column=0, sticky="w", pady=(4, 0))
            ctk.CTkLabel(
                details,
                text=f"Updated {self._format_modified_date(record.updated_at)}",
                font=self.font_small,
                text_color=COLORS["muted"],
                anchor="w",
            ).grid(row=2, column=0, sticky="w", pady=(4, 0))

            card_actions = ctk.CTkFrame(card, fg_color="transparent")
            card_actions.grid(row=0, column=1, sticky="e", padx=(8, 16))
            self._button(
                card_actions,
                text="Open",
                command=lambda value=record.id: self.open_library_document(value),
                variant="secondary",
                width=60,
                height=34,
            ).pack(side="left", padx=(0, 4))
            self._button(
                card_actions,
                text="Rename",
                command=lambda value=record.id: self.rename_cv(value),
                variant="ghost",
                width=68,
                height=34,
            ).pack(side="left")
            self._button(
                card_actions,
                text="Delete",
                command=lambda value=record.id: self.delete_cv(value),
                variant="danger",
                width=58,
                height=34,
            ).pack(side="left")
        self.library_scroll._schedule_scrollbar_check()

    def _build_sections(self):
        self._build_profile_section()
        self._build_summary_section()
        self._build_experience_section()
        self._build_education_section()
        for frame in self.section_frames.values():
            frame.grid(row=0, column=0, sticky="nsew")

    def _new_section(self, key: str) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(
            self.content_host,
            corner_radius=0,
            fg_color=COLORS["background"],
        )
        frame.grid_columnconfigure(0, weight=1)
        self.section_frames[key] = frame
        return frame

    def _add_section_header(
        self,
        parent,
        *,
        step: str,
        title: str | tk.StringVar,
        subtitle: str | tk.StringVar,
        action_text: str | None = None,
        action_command=None,
    ):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=36, pady=(27, 18))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header,
            text=step.upper(),
            font=self.font_small_bold,
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        title_options = (
            {"textvariable": title} if isinstance(title, tk.StringVar) else {"text": title}
        )
        ctk.CTkLabel(
            header,
            font=self.font_page_title,
            text_color=COLORS["text"],
            anchor="w",
            **title_options,
        ).grid(row=1, column=0, sticky="w", pady=(4, 3))
        subtitle_options = (
            {"textvariable": subtitle}
            if isinstance(subtitle, tk.StringVar)
            else {"text": subtitle}
        )
        ctk.CTkLabel(
            header,
            font=self.font_body,
            text_color=COLORS["muted"],
            anchor="w",
            **subtitle_options,
        ).grid(row=2, column=0, sticky="w")
        if action_text:
            button = self._button(
                header,
                text=action_text,
                command=action_command,
                variant="primary",
                width=120,
            )
            button.grid(row=0, column=1, rowspan=3, sticky="e")
            return button
        return None

    def _card(self, parent, **kwargs) -> ctk.CTkFrame:
        return ctk.CTkFrame(
            parent,
            corner_radius=13,
            fg_color=COLORS["surface"],
            border_width=1,
            border_color=COLORS["border"],
            **kwargs,
        )

    def _new_tracked_var(self) -> tk.StringVar:
        variable = tk.StringVar()
        variable.trace_add("write", self._on_variable_changed)
        return variable

    def _form_field(
        self,
        parent,
        *,
        label: str,
        variable: tk.StringVar,
        row: int,
        column: int = 0,
        columnspan: int = 1,
        padx=(0, 0),
        pady=(0, 14),
        placeholder: str = "",
    ) -> PlaceholderEntry:
        group = ctk.CTkFrame(parent, fg_color="transparent")
        group.grid(
            row=row,
            column=column,
            columnspan=columnspan,
            sticky="ew",
            padx=padx,
            pady=pady,
        )
        group.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            group,
            text=label,
            font=self.font_label,
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", pady=(0, 6))
        entry = PlaceholderEntry(
            group,
            textvariable=variable,
            height=42,
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
            fg_color=COLORS["surface"],
            text_color=COLORS["text"],
            placeholder_text=placeholder,
            placeholder_text_color=COLORS["muted"],
            font=self.font_body,
        )
        entry.grid(row=1, column=0, sticky="ew")
        return entry

    def _textbox(
        self,
        parent,
        *,
        height: int,
        placeholder: str = "",
    ) -> PlaceholderTextbox:
        return PlaceholderTextbox(
            parent,
            height=height,
            placeholder_text=placeholder,
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
            fg_color=COLORS["surface"],
            text_color=COLORS["text"],
            font=self.font_body,
            wrap="word",
            undo=True,
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["muted"],
        )

    def _build_profile_section(self):
        section = self._new_section("profile")
        self._add_section_header(
            section,
            step="Section 1 of 4",
            title="Profile",
            subtitle="The essential details shown at the top of your CV.",
        )
        card = self._card(section)
        card.grid(row=1, column=0, sticky="new", padx=36, pady=(0, 30))
        card.grid_columnconfigure((0, 1), weight=1, uniform="profile")

        for key in ("name", "headline", "location", "email", "linkedin"):
            self.profile_vars[key] = self._new_tracked_var()

        self.profile_entries["name"] = self._form_field(
            card,
            label="Full name",
            variable=self.profile_vars["name"],
            placeholder=PLACEHOLDERS["name"],
            row=0,
            columnspan=2,
            padx=22,
            pady=(22, 14),
        )
        self.profile_entries["headline"] = self._form_field(
            card,
            label="Professional headline",
            variable=self.profile_vars["headline"],
            placeholder=PLACEHOLDERS["headline"],
            row=1,
            columnspan=2,
            padx=22,
        )
        self.profile_entries["location"] = self._form_field(
            card,
            label="Location",
            variable=self.profile_vars["location"],
            placeholder=PLACEHOLDERS["location"],
            row=2,
            column=0,
            padx=(22, 7),
        )
        self.profile_entries["email"] = self._form_field(
            card,
            label="Email",
            variable=self.profile_vars["email"],
            placeholder=PLACEHOLDERS["email"],
            row=2,
            column=1,
            padx=(7, 22),
        )
        self.profile_entries["linkedin"] = self._form_field(
            card,
            label="LinkedIn or website",
            variable=self.profile_vars["linkedin"],
            placeholder=PLACEHOLDERS["linkedin"],
            row=3,
            columnspan=2,
            padx=22,
        )

        skills_group = ctk.CTkFrame(card, fg_color="transparent")
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
            font=self.font_label,
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            skills_group,
            text="One skill per line",
            font=self.font_small,
            text_color=COLORS["muted"],
            anchor="e",
        ).grid(row=0, column=1, sticky="e")
        self.skills_text = self._textbox(
            skills_group,
            height=118,
            placeholder=PLACEHOLDERS["skills"],
        )
        self.skills_text.grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0)
        )
        self.skills_text.bind(
            "<KeyRelease>", lambda _event: self._on_main_text_changed(), add="+"
        )

    def _build_summary_section(self):
        section = self._new_section("summary")
        section.grid_rowconfigure(1, weight=1)
        self._add_section_header(
            section,
            step="Section 2 of 4",
            title="Summary",
            subtitle="Use a blank line between paragraphs.",
        )
        card = self._card(section)
        card.grid(row=1, column=0, sticky="nsew", padx=36, pady=(0, 30))
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(
            card,
            text="Professional summary",
            font=self.font_label,
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=22, pady=(22, 7))
        self.summary_text = self._textbox(
            card,
            height=400,
            placeholder=PLACEHOLDERS["summary"],
        )
        self.summary_text.grid(row=1, column=0, sticky="nsew", padx=22)
        self.summary_text.bind(
            "<KeyRelease>",
            lambda _event: self._on_main_text_changed(summary=True),
            add="+",
        )
        ctk.CTkLabel(
            card,
            textvariable=self.summary_count,
            font=self.font_small,
            text_color=COLORS["muted"],
            anchor="e",
        ).grid(row=2, column=0, sticky="e", padx=22, pady=(8, 18))

    def _build_experience_section(self):
        section = self._new_section("experience")
        section.grid_rowconfigure(1, weight=1)
        self.experience_add_button = self._add_section_header(
            section,
            step="Section 3 of 4",
            title=self.experience_title,
            subtitle=self.experience_subtitle,
            action_text="+  Add role",
            action_command=self.add_experience,
        )

        self.experience_stack = ctk.CTkFrame(
            section, fg_color="transparent", corner_radius=0
        )
        self.experience_stack.grid(
            row=1, column=0, sticky="nsew", padx=36, pady=(0, 28)
        )
        self.experience_stack.grid_columnconfigure(0, weight=1)
        self.experience_stack.grid_rowconfigure(0, weight=1)

        self.experience_list_view = ctk.CTkFrame(
            self.experience_stack, fg_color="transparent", corner_radius=0
        )
        self.experience_list_view.grid(row=0, column=0, sticky="nsew")
        self.experience_list_view.grid_columnconfigure(0, weight=1)
        self.experience_list_view.grid_rowconfigure(0, weight=1)
        self.experience_scroll = AutoHideScrollableFrame(
            self.experience_list_view,
            width=600,
            height=420,
            corner_radius=0,
            fg_color="transparent",
            scrollbar_fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["muted"],
        )
        self.experience_scroll.grid(row=0, column=0, sticky="nsew")
        self.experience_scroll.grid_columnconfigure(0, weight=1)

        self.experience_editor_view = ctk.CTkFrame(
            self.experience_stack, fg_color="transparent", corner_radius=0
        )
        self.experience_editor_view.grid(row=0, column=0, sticky="nsew")
        self.experience_editor_view.grid_columnconfigure(0, weight=1)
        self.experience_editor_view.grid_rowconfigure(0, weight=1)

        self.editor_scroll = AutoHideScrollableFrame(
            self.experience_editor_view,
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

        editor_card = self._card(self.editor_scroll)
        editor_card.grid(row=0, column=0, sticky="new", padx=(0, 8), pady=(0, 12))
        editor_card.grid_columnconfigure((0, 1), weight=1, uniform="experience")

        for key in ("company", "duration", "role", "dates", "place"):
            self.editor_vars[key] = tk.StringVar()

        self.editor_company_entry = self._form_field(
            editor_card,
            label="Company",
            variable=self.editor_vars["company"],
            placeholder=PLACEHOLDERS["company"],
            row=0,
            columnspan=2,
            padx=22,
            pady=(22, 12),
        )
        self._form_field(
            editor_card,
            label="Role",
            variable=self.editor_vars["role"],
            placeholder=PLACEHOLDERS["role"],
            row=1,
            columnspan=2,
            padx=22,
            pady=(0, 12),
        )
        self._form_field(
            editor_card,
            label="Dates",
            variable=self.editor_vars["dates"],
            placeholder=PLACEHOLDERS["dates"],
            row=2,
            column=0,
            padx=(22, 7),
            pady=(0, 12),
        )
        self._form_field(
            editor_card,
            label="Total duration",
            variable=self.editor_vars["duration"],
            placeholder=PLACEHOLDERS["duration"],
            row=2,
            column=1,
            padx=(7, 22),
            pady=(0, 12),
        )
        self._form_field(
            editor_card,
            label="Location",
            variable=self.editor_vars["place"],
            placeholder=PLACEHOLDERS["place"],
            row=3,
            columnspan=2,
            padx=22,
            pady=(0, 12),
        )

        self.editor_texts: dict[str, ctk.CTkTextbox] = {}
        text_fields = (
            ("Role or project description", "intro", 72, None),
            ("Key responsibilities", "work", 94, "One item per line"),
            ("Results", "results", 86, "One item per line"),
        )
        for row, (label, key, height, hint) in enumerate(text_fields, start=4):
            group = ctk.CTkFrame(editor_card, fg_color="transparent")
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
                font=self.font_label,
                text_color=COLORS["text"],
                anchor="w",
            ).grid(row=0, column=0, sticky="w")
            if hint:
                ctk.CTkLabel(
                    group,
                    text=hint,
                    font=self.font_small,
                    text_color=COLORS["muted"],
                    anchor="e",
                ).grid(row=0, column=1, sticky="e")
            widget = self._textbox(
                group,
                height=height,
                placeholder=PLACEHOLDERS[key],
            )
            widget.grid(
                row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0)
            )
            self.editor_texts[key] = widget

        editor_actions = ctk.CTkFrame(
            self.experience_editor_view,
            fg_color=COLORS["background"],
            corner_radius=0,
        )
        editor_actions.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        self._button(
            editor_actions,
            text="Save entry",
            command=self.save_experience_entry,
            variant="primary",
            width=106,
        ).pack(side="right")
        self._button(
            editor_actions,
            text="Cancel",
            command=self.cancel_experience_edit,
            variant="secondary",
            width=76,
        ).pack(side="right", padx=(0, 8))

    def _build_education_section(self):
        section = self._new_section("education")
        self._add_section_header(
            section,
            step="Section 4 of 4",
            title="Education",
            subtitle="Add the qualification most relevant to this CV.",
        )
        card = self._card(section)
        card.grid(row=1, column=0, sticky="new", padx=36, pady=(0, 30))
        card.grid_columnconfigure(0, weight=1)

        for key in ("institution", "qualification"):
            self.education_vars[key] = self._new_tracked_var()
        self._form_field(
            card,
            label="Institution",
            variable=self.education_vars["institution"],
            placeholder=PLACEHOLDERS["institution"],
            row=0,
            padx=22,
            pady=(22, 14),
        )
        self._form_field(
            card,
            label="Qualification and dates",
            variable=self.education_vars["qualification"],
            placeholder=PLACEHOLDERS["qualification"],
            row=1,
            padx=22,
            pady=(0, 22),
        )

    def show_library(self):
        self._save_now()
        self.refresh_library()
        self.library_view.tkraise()
        self.status.set("Local CV library")

    def create_cv(self):
        try:
            record = self.library.create_document()
            self.open_library_document(record.id)
        except Exception as error:
            messagebox.showerror("Could not create CV", str(error), parent=self)

    def open_library_document(self, document_id: str):
        self._cancel_autosave()
        try:
            record = self.library.get_record(document_id)
            self.data = self.library.load_document(document_id)
        except Exception as error:
            messagebox.showerror("Could not open CV", str(error), parent=self)
            return
        self.current_document_id = record.id
        self.current_document_title = record.title
        self.populate_form()
        self.show_section("profile")
        self.editor_view.tkraise()
        self.status.set(f"{record.title}  ·  Saved")

    def rename_cv(self, document_id: str):
        try:
            record = self.library.get_record(document_id)
        except Exception as error:
            messagebox.showerror("Could not rename CV", str(error), parent=self)
            return
        dialog = ctk.CTkInputDialog(
            text="Enter a new name for this CV:",
            title="Rename CV",
        )
        value = dialog.get_input()
        if value is None:
            return
        try:
            updated = self.library.rename_document(document_id, value)
            if self.current_document_id == document_id:
                self.current_document_title = updated.title
            self.refresh_library()
        except Exception as error:
            messagebox.showerror("Could not rename CV", str(error), parent=self)

    def delete_cv(self, document_id: str):
        try:
            record = self.library.get_record(document_id)
        except Exception:
            self.refresh_library()
            return
        if not messagebox.askyesno(
            "Delete CV",
            f'Delete "{record.title}" from this device?',
            detail="This cannot be undone. Export its JSON first if you need a backup.",
            parent=self,
        ):
            return
        try:
            self.library.delete_document(document_id)
            if self.current_document_id == document_id:
                self.current_document_id = None
                self.current_document_title = ""
                self.data = new_document()
            self.refresh_library()
        except Exception as error:
            messagebox.showerror("Could not delete CV", str(error), parent=self)

    def import_json(self):
        path = filedialog.askopenfilename(
            title="Import CV JSON",
            filetypes=[("CV Builder JSON", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            record = self.library.import_document(path)
            self.open_library_document(record.id)
        except Exception as error:
            messagebox.showerror("Could not import JSON", str(error), parent=self)

    def export_example_json(self):
        path = filedialog.asksaveasfilename(
            title="Save example CV JSON",
            defaultextension=".json",
            initialfile="cv-builder-example.json",
            filetypes=[("CV Builder JSON", "*.json")],
        )
        if not path:
            return False
        try:
            save_document(path, example_document())
            messagebox.showinfo(
                "Example JSON saved",
                f"Edit this file and import it back into CV Builder:\n{path}",
                parent=self,
            )
            return True
        except Exception as error:
            messagebox.showerror(
                "Could not save example JSON", str(error), parent=self
            )
            return False

    def export_current_json(self):
        if self.current_document_id is None:
            return False
        suggested = (
            self.current_document_title.strip().replace("/", "-") or "my-cv"
        )
        path = filedialog.asksaveasfilename(
            title="Export CV JSON",
            defaultextension=".json",
            initialfile=f"{suggested}.json",
            filetypes=[("CV Builder JSON", "*.json")],
        )
        if not path:
            return False
        try:
            self._save_now()
            save_document(path, self.collect_form())
            self.status.set(
                f"{self.current_document_title}  ·  JSON exported"
            )
            return True
        except Exception as error:
            messagebox.showerror("Could not export JSON", str(error), parent=self)
            return False

    def _bind_shortcuts(self):
        self.bind_all("<Control-s>", lambda _event: self.save_file())
        self.bind_all("<Command-s>", lambda _event: self.save_file())
        self.bind_all("<Control-o>", lambda _event: self.show_library())
        self.bind_all("<Command-o>", lambda _event: self.show_library())
        self.bind_all("<Escape>", self._handle_escape)

    def _handle_escape(self, _event=None):
        if self.current_section == "experience" and self.experience_editor_open:
            self.cancel_experience_edit()

    def show_section(self, section: str):
        if section not in self.section_frames:
            raise ValueError(f"Unknown section: {section}")
        self.current_section = section
        self.section_frames[section].tkraise()
        for name, button in self.nav_buttons.items():
            active = name == section
            button.configure(
                fg_color=COLORS["selection"] if active else "transparent",
                text_color=COLORS["accent"] if active else COLORS["muted"],
                font=self.font_nav_active if active else self.font_nav,
            )

    def _show_experience_list(self):
        self.experience_editor_open = False
        self.experience_title.set("Experience")
        self.experience_subtitle.set("Put the most relevant role first.")
        self.experience_add_button.grid()
        self.experience_list_view.tkraise()
        self.experience_scroll._schedule_scrollbar_check()

    def _show_experience_editor(self, *, is_new: bool):
        self.experience_editor_open = True
        self.experience_title.set("Add experience" if is_new else "Edit experience")
        self.experience_subtitle.set(
            "Describe the role, responsibilities and measurable results."
        )
        self.experience_add_button.grid_remove()
        self.experience_editor_view.tkraise()
        self.editor_scroll._schedule_scrollbar_check()
        self.after_idle(self.editor_company_entry.focus_set)

    def _on_variable_changed(self, *_args):
        if not self._loading:
            self._mark_dirty()

    def _on_main_text_changed(self, *, summary: bool = False):
        if summary:
            self._update_summary_count()
        if not self._loading:
            self._mark_dirty()

    def _mark_dirty(self):
        if self.current_document_id is None:
            return
        self.status.set(f"{self.current_document_title}  ·  Saving…")
        self._schedule_progress_update()
        self._schedule_autosave()

    def _schedule_autosave(self):
        self._cancel_autosave()
        self._autosave_job = self.after(650, self._save_now)

    def _cancel_autosave(self):
        if self._autosave_job:
            try:
                self.after_cancel(self._autosave_job)
            except tk.TclError:
                pass
            self._autosave_job = None

    def _save_now(self):
        self._cancel_autosave()
        if self.current_document_id is None:
            return False
        try:
            self.library.save_document(
                self.current_document_id,
                self.collect_form(),
            )
            self.status.set(f"{self.current_document_title}  ·  Saved")
            return True
        except Exception:
            self.status.set(f"{self.current_document_title}  ·  Save failed")
            return False

    def _close_application(self):
        self._save_now()
        self.destroy()

    def _schedule_progress_update(self):
        if self._progress_job:
            self.after_cancel(self._progress_job)
        self._progress_job = self.after(80, self._update_progress)

    def _update_progress(self):
        self._progress_job = None
        percent = calculate_completion(self.collect_form())
        self.progress_bar.configure(
            progress_color=COLORS["accent"] if percent else COLORS["border"]
        )
        self.progress_bar.set(percent / 100)
        self.progress_text.set(f"{percent}% complete")

    def _update_summary_count(self):
        value = self.summary_text.get("1.0", "end-1c")
        count = len(value)
        self.summary_count.set(
            f"{count} character" if count == 1 else f"{count} characters"
        )

    def collect_form(self):
        profile = self.data["profile"]
        for key, variable in self.profile_vars.items():
            profile[key] = variable.get().strip()
        profile["skills"] = split_lines(self.skills_text.get("1.0", "end"))
        profile["summary"] = split_paragraphs(self.summary_text.get("1.0", "end"))
        for key, variable in self.education_vars.items():
            self.data["education"][key] = variable.get().strip()
        return self.data

    def populate_form(self):
        self._loading = True
        profile = self.data["profile"]
        for key, variable in self.profile_vars.items():
            variable.set(profile.get(key, ""))
        self.skills_text.set_value("\n".join(profile.get("skills", [])))
        self.summary_text.set_value("\n\n".join(profile.get("summary", [])))
        for key, variable in self.education_vars.items():
            variable.set(self.data["education"].get(key, ""))
        self.refresh_experience()
        self._show_experience_list()
        self._update_summary_count()
        self._loading = False
        self._update_progress()

    def refresh_experience(self, selection=None):
        self.experience_selection = selection
        for child in self.experience_scroll.winfo_children():
            child.destroy()
        self.experience_scroll.grid_columnconfigure(0, weight=1)

        entries = self.data["experience"]
        if not entries:
            empty = self._card(self.experience_scroll)
            empty.grid(row=0, column=0, sticky="ew", padx=(0, 8))
            empty.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                empty,
                text="No experience added yet",
                font=self.font_card_title,
                text_color=COLORS["text"],
            ).grid(row=0, column=0, pady=(28, 4))
            ctk.CTkLabel(
                empty,
                text="Add a role to show your responsibilities and impact.",
                font=self.font_small,
                text_color=COLORS["muted"],
            ).grid(row=1, column=0)
            self._button(
                empty,
                text="+  Add your first role",
                command=self.add_experience,
                variant="primary",
                width=154,
            ).grid(row=2, column=0, pady=(16, 28))
            self.experience_scroll._schedule_scrollbar_check()
            return

        for index, item in enumerate(entries):
            card = self._card(self.experience_scroll)
            card.grid(
                row=index,
                column=0,
                sticky="ew",
                padx=(0, 8),
                pady=(0, 10),
            )
            card.grid_columnconfigure(0, weight=1)
            content = ctk.CTkFrame(card, fg_color="transparent")
            content.grid(row=0, column=0, sticky="ew", padx=18, pady=16)
            content.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                content,
                text=item.get("role") or "Untitled role",
                font=self.font_card_title,
                text_color=COLORS["text"],
                anchor="w",
            ).grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(
                content,
                text=item.get("company") or "Company not specified",
                font=self.font_body,
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
                    font=self.font_small,
                    text_color=COLORS["muted"],
                    anchor="w",
                ).grid(row=2, column=0, sticky="w", pady=(4, 0))

            actions = ctk.CTkFrame(card, fg_color="transparent")
            actions.grid(row=0, column=1, sticky="e", padx=(8, 14))
            self._button(
                actions,
                text="Edit",
                command=lambda value=index: self.edit_experience(value),
                variant="secondary",
                width=56,
                height=34,
            ).pack(side="left", padx=(0, 4))
            self._button(
                actions,
                text="↑",
                command=lambda value=index: self.move_experience(-1, value),
                variant="ghost",
                width=34,
                height=34,
            ).pack(side="left")
            self._button(
                actions,
                text="↓",
                command=lambda value=index: self.move_experience(1, value),
                variant="ghost",
                width=34,
                height=34,
            ).pack(side="left")
            self._button(
                actions,
                text="Delete",
                command=lambda value=index: self.delete_experience(value),
                variant="danger",
                width=60,
                height=34,
            ).pack(side="left", padx=(3, 0))
        self.experience_scroll._schedule_scrollbar_check()

    def selected_index(self):
        return self.experience_selection

    def _load_experience_editor(self, item: dict):
        for key, variable in self.editor_vars.items():
            variable.set(item.get(key, ""))
        values = {
            "intro": item.get("intro", ""),
            "work": "\n".join(item.get("work", [])),
            "results": "\n".join(item.get("results", [])),
        }
        for key, widget in self.editor_texts.items():
            widget.set_value(values[key])

    def add_experience(self):
        self.editing_experience_index = None
        self.experience_selection = None
        self._load_experience_editor(empty_experience())
        self._show_experience_editor(is_new=True)

    def edit_experience(self, index=None):
        if index is None:
            index = self.selected_index()
        if index is None or not 0 <= index < len(self.data["experience"]):
            messagebox.showinfo(
                "Select an entry",
                "Select an experience entry first.",
                parent=self,
            )
            return
        self.editing_experience_index = index
        self.experience_selection = index
        self._load_experience_editor(deepcopy(self.data["experience"][index]))
        self._show_experience_editor(is_new=False)

    def cancel_experience_edit(self):
        self.editing_experience_index = None
        self._show_experience_list()

    def save_experience_entry(self):
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
                "results": split_lines(
                    self.editor_texts["results"].get("1.0", "end")
                ),
            }
        )
        if self.editing_experience_index is None:
            self.data["experience"].append(item)
            selection = len(self.data["experience"]) - 1
        else:
            self.data["experience"][self.editing_experience_index] = item
            selection = self.editing_experience_index
        self.editing_experience_index = None
        self.refresh_experience(selection)
        self._show_experience_list()
        self._mark_dirty()

    def delete_experience(self, index=None):
        if index is None:
            index = self.selected_index()
        if index is None or not 0 <= index < len(self.data["experience"]):
            return
        if messagebox.askyesno(
            "Delete entry",
            "Delete this experience entry?",
            parent=self,
        ):
            del self.data["experience"][index]
            self.refresh_experience(
                min(index, len(self.data["experience"]) - 1)
                if self.data["experience"]
                else None
            )
            self._mark_dirty()

    def move_experience(self, direction, index=None):
        if index is None:
            index = self.selected_index()
        target = index + direction if index is not None else -1
        if index is None or target < 0 or target >= len(self.data["experience"]):
            return
        entries = self.data["experience"]
        entries[index], entries[target] = entries[target], entries[index]
        self.refresh_experience(target)
        self._mark_dirty()

    def new_file(self):
        self.create_cv()

    def open_file(self):
        self.import_json()

    def save_file(self):
        return self._save_now()

    def save_as(self):
        return self.export_current_json()

    def generate(self):
        data = self.collect_form()
        if not data["profile"].get("name"):
            messagebox.showwarning(
                "Missing name",
                "Enter a name before generating the PDF.",
                parent=self,
            )
            return
        path = filedialog.asksaveasfilename(
            title="Export PDF",
            defaultextension=".pdf",
            initialfile=f"{data['profile']['name']} - CV.pdf",
            filetypes=[("PDF document", "*.pdf")],
        )
        if not path:
            return
        try:
            self.status.set("Exporting PDF…")
            self.update_idletasks()
            generate_pdf(data, path)
            self.status.set(f"Exported · {Path(path).name}")
            messagebox.showinfo(
                "PDF created",
                f"Your CV was saved to:\n{path}",
                parent=self,
            )
        except Exception as error:
            self.status.set("PDF export failed")
            messagebox.showerror("Could not generate PDF", str(error), parent=self)


def run_packaged_ui_smoke(output: Path) -> None:
    """Exercise frozen UI layout and persist diagnostics without user input."""
    from tempfile import TemporaryDirectory

    temporary = TemporaryDirectory(prefix="cvbuilder-packaged-smoke-")
    library = CVLibrary(temporary.name)
    record = library.create_document("Packaged Smoke CV", example_document())
    app = CVBuilderApp(library=library)

    def exercise() -> None:
        app.update_idletasks()
        placeholders_are_data = any(
            (
                app.profile_vars["name"].get(),
                app.skills_text.get("1.0", "end-1c"),
                app.summary_text.get("1.0", "end-1c"),
            )
        )
        library_size = {
            "width": app.library_view.winfo_width(),
            "height": app.library_view.winfo_height(),
        }
        app.open_library_document(record.id)
        app.update_idletasks()
        sections = {}
        for section in SECTION_ORDER:
            app.show_section(section)
            app.update_idletasks()
            frame = app.section_frames[section]
            sections[section] = {
                "width": frame.winfo_width(),
                "height": frame.winfo_height(),
            }
        app.show_section("experience")
        app.edit_experience(0)
        app.update_idletasks()
        result = {
            "tk_version": tk.TkVersion,
            "library": library_size,
            "library_document_count": len(library.list_documents()),
            "placeholders_are_data": placeholders_are_data,
            "window": {
                "width": app.winfo_width(),
                "height": app.winfo_height(),
            },
            "sections": sections,
            "experience_editor_open": app.experience_editor_open,
        }
        output.write_text(json.dumps(result, indent=2), encoding="utf-8")
        app.destroy()

    app.after(180, exercise)
    app.mainloop()
    temporary.cleanup()


if __name__ == "__main__":
    if "--ui-smoke-test" in sys.argv:
        index = sys.argv.index("--ui-smoke-test")
        output = (
            Path(sys.argv[index + 1])
            if len(sys.argv) > index + 1
            else Path.cwd() / "CVBuilder-ui-smoke.json"
        )
        run_packaged_ui_smoke(output)
    elif "--smoke-test" in sys.argv:
        index = sys.argv.index("--smoke-test")
        output = (
            Path(sys.argv[index + 1])
            if len(sys.argv) > index + 1
            else Path.cwd() / "CVBuilder-smoke-test.pdf"
        )
        generate_pdf(new_document(), output)
    else:
        CVBuilderApp().mainloop()
