"""The CV editor: header, step navigation and the five sections."""
from __future__ import annotations

from typing import Any

import customtkinter as ctk

from cv_builder.ui.screens.sections.education import EducationSection
from cv_builder.ui.screens.sections.experience import ExperienceSection
from cv_builder.ui.screens.sections.preview import PreviewSection
from cv_builder.ui.screens.sections.profile import ProfileSection
from cv_builder.ui.screens.sections.summary import SummarySection
from cv_builder.ui.theme import COLORS, button


SECTION_ORDER = ("profile", "summary", "experience", "education", "preview")
# Nav copy lives in `ui/strings/`; the order is what this module owns.
# Sections that hold form data; `preview` renders them.
FORM_SECTIONS = SECTION_ORDER[:-1]


class EditorScreen(ctk.CTkFrame):
    """Owns the form widgets; the application owns the document."""

    def __init__(self, master, *, controller):
        super().__init__(master, corner_radius=0, fg_color=COLORS["background"])
        self.controller = controller
        self.fonts = controller.fonts
        self.t = controller.t
        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        self.sections: dict[str, Any] = {}
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_header()
        self._build_workspace()
        self._build_sections()

    # --- header ----------------------------------------------------------

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, height=64, corner_radius=0, fg_color=COLORS["surface"])
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(2, weight=1)
        ctk.CTkLabel(
            header,
            text=self.t("app.name"),
            font=self.fonts.brand,
            text_color=COLORS["text"],
        ).grid(row=0, column=0, sticky="w", padx=(20, 0), pady=12)
        self.title_entry = ctk.CTkEntry(
            header,
            textvariable=self.controller.document_title_var,
            font=self.fonts.card_title,
            width=260,
            height=30,
            corner_radius=8,
            fg_color=COLORS["surface"],
            border_width=0,
            text_color=COLORS["text"],
            state="disabled",
        )
        self.title_entry.grid(row=0, column=1, sticky="w", padx=(18, 8))
        self._bind_title_entry()
        ctk.CTkLabel(
            header,
            textvariable=self.controller.status,
            font=self.fonts.small,
            text_color=COLORS["muted"],
        ).grid(row=0, column=2, sticky="w", padx=(2, 10))

        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.grid(row=0, column=3, sticky="e", padx=(0, 18), pady=11)
        button(
            actions,
            self.fonts,
            text=self.t("editor.all_cvs"),
            command=self.controller.show_library,
            variant="ghost",
            width=70,
        ).pack(side="left", padx=(0, 5))
        button(
            actions,
            self.fonts,
            text=self.t("editor.export_json"),
            command=self.controller.export_current_json,
            variant="secondary",
            width=96,
        ).pack(side="left", padx=(0, 8))
        # Hidden on the preview step, which carries its own Export CTA.
        self.export_pdf_button = button(
            actions,
            self.fonts,
            text=self.t("editor.export_pdf"),
            command=self.controller.generate,
            variant="primary",
            width=112,
        )
        self.export_pdf_button.pack(side="left")

    def _bind_title_entry(self) -> None:
        """Make the header title look flat until hovered or focused."""
        entry = self.title_entry
        entry.bind("<Enter>", lambda _event: self.style_title_entry(True))
        entry.bind("<Leave>", lambda _event: self.style_title_entry(False))
        entry.bind("<FocusIn>", lambda _event: self.style_title_entry(True))
        entry.bind("<FocusOut>", self._on_title_focus_out)
        entry.bind("<Return>", self._on_title_return)
        entry.bind("<Escape>", self._on_title_escape)

    def style_title_entry(self, active: bool) -> None:
        if self.title_entry.cget("state") == "disabled":
            return
        if active:
            self.title_entry.configure(
                fg_color=COLORS["surface_alt"],
                border_width=1,
                border_color=COLORS["border"],
            )
            return
        if self.winfo_toplevel().focus_get() is not self.title_entry._entry:
            self.title_entry.configure(fg_color=COLORS["surface"], border_width=0)

    def set_title_editable(self, editable: bool) -> None:
        if editable:
            self.title_entry.configure(state="normal")
        else:
            self.title_entry.configure(
                state="disabled", fg_color=COLORS["surface"], border_width=0
            )

    def _on_title_focus_out(self, _event=None):
        self.controller.commit_title_edit()
        self.style_title_entry(False)

    def _on_title_return(self, _event=None):
        self.controller.commit_title_edit()
        self.winfo_toplevel().focus_set()
        return "break"

    def _on_title_escape(self, _event=None):
        self.controller.reset_title_field()
        self.winfo_toplevel().focus_set()
        return "break"

    # --- workspace -------------------------------------------------------

    def _build_workspace(self) -> None:
        workspace = ctk.CTkFrame(self, corner_radius=0, fg_color=COLORS["background"])
        workspace.grid(row=1, column=0, sticky="nsew")
        workspace.grid_columnconfigure(1, weight=1)
        workspace.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(
            workspace, width=218, corner_radius=0, fg_color=COLORS["surface_alt"]
        )
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)
        sidebar.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(
            sidebar,
            text=self.t("editor.build_your_cv"),
            font=self.fonts.small_bold,
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=22, pady=(28, 0))
        ctk.CTkLabel(
            sidebar,
            textvariable=self.controller.progress_text,
            font=self.fonts.body,
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
        for row, section in enumerate(SECTION_ORDER):
            nav_button = ctk.CTkButton(
                navigation,
                text=self.t(f"nav.{section}"),
                command=lambda value=section: self.controller.show_section(value),
                height=44,
                corner_radius=9,
                fg_color="transparent",
                hover_color=COLORS["surface"],
                text_color=COLORS["muted"],
                font=self.fonts.nav,
                anchor="w",
                border_spacing=12,
            )
            nav_button.grid(row=row, column=0, sticky="ew", pady=2)
            self.nav_buttons[section] = nav_button

        ctk.CTkLabel(
            sidebar,
            text=self.t("editor.privacy"),
            font=self.fonts.small,
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

    def _build_sections(self) -> None:
        classes = {
            "profile": ProfileSection,
            "summary": SummarySection,
            "experience": ExperienceSection,
            "education": EducationSection,
            "preview": PreviewSection,
        }
        for key, section_class in classes.items():
            section = section_class(
                self.content_host,
                fonts=self.fonts,
                on_change=self.controller.on_form_changed,
                controller=self.controller,
            )
            section.grid(row=0, column=0, sticky="nsew")
            self.sections[key] = section
        self.profile = self.sections["profile"]
        self.summary = self.sections["summary"]
        self.experience = self.sections["experience"]
        self.education = self.sections["education"]
        self.preview = self.sections["preview"]

    # --- document --------------------------------------------------------

    def show_section(self, section: str) -> None:
        if section not in self.sections:
            raise ValueError(f"Unknown section: {section}")
        self.sections[section].tkraise()
        if section == "preview":
            self.export_pdf_button.pack_forget()
        elif not self.export_pdf_button.winfo_ismapped():
            self.export_pdf_button.pack(side="left")
        for name, nav_button in self.nav_buttons.items():
            active = name == section
            nav_button.configure(
                fg_color=COLORS["selection"] if active else "transparent",
                text_color=COLORS["accent"] if active else COLORS["muted"],
                font=self.fonts.nav_active if active else self.fonts.nav,
            )

    def collect(self, data: dict[str, Any]) -> dict[str, Any]:
        for key in FORM_SECTIONS:
            self.sections[key].collect(data)
        return data

    def populate(self, data: dict[str, Any]) -> None:
        for section in self.sections.values():
            section.populate(data)

    def set_progress(self, percent: int) -> None:
        self.progress_bar.configure(
            progress_color=COLORS["accent"] if percent else COLORS["border"]
        )
        self.progress_bar.set(percent / 100)
