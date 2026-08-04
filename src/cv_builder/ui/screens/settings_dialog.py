"""Application settings: the interface language and the import example.

Deliberately a separate window from the editor: everything on the editor's five
steps belongs to one CV, while what is here applies to the installation.
"""
from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from cv_builder.domain import locales
from cv_builder.ui.components.fields import option_menu
from cv_builder.ui.theme import COLORS, button


BODY_WIDTH = 380


class SettingsDialog(ctk.CTkToplevel):
    """Modal preferences window owned by the application shell."""

    def __init__(self, master, *, controller):
        super().__init__(master, fg_color=COLORS["background"])
        self.controller = controller
        self.t = controller.t
        self.title(self.t("settings.title"))
        self.resizable(False, False)
        self.grid_columnconfigure(0, weight=1)

        self.language = tk.StringVar(
            value=locales.locale_label(controller.settings.ui_locale)
        )
        self._build()
        self.transient(master)
        self.after(80, self._grab)

    def _grab(self) -> None:
        try:
            self.grab_set()
        except tk.TclError:
            pass  # The window may already be gone in a headless smoke run.

    def _without_grab(self, action):
        """Run a nested dialog outside this window's modal grab.

        A `transient` child stays above its master on macOS, so a file chooser
        or a message box owned by the application window would open *behind*
        Settings and be half-hidden. Releasing the grab for the call — and
        raising this window again afterwards — keeps the stack honest.
        """
        try:
            self.grab_release()
        except tk.TclError:
            pass
        try:
            return action()
        finally:
            if self.winfo_exists():
                self.lift()
                self.focus_force()
                self._grab()

    def _build(self) -> None:
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=0, column=0, sticky="nsew", padx=28, pady=(26, 0))
        body.grid_columnconfigure(0, weight=1)
        self._build_language(body)
        self._build_example_json(body)

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=1, column=0, sticky="e", padx=28, pady=(20, 22))
        button(
            footer,
            self.controller.fonts,
            text=self.t("action.done"),
            command=self.destroy,
            variant="primary",
            width=92,
        ).pack(side="right")

    def _heading(self, parent, row: int, key: str, pady) -> None:
        ctk.CTkLabel(
            parent,
            text=self.t(key),
            font=self.controller.fonts.label,
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=row, column=0, sticky="w", pady=pady)

    def _hint(self, parent, row: int, key: str, pady) -> None:
        ctk.CTkLabel(
            parent,
            text=self.t(key),
            font=self.controller.fonts.small,
            text_color=COLORS["muted"],
            anchor="w",
            justify="left",
            wraplength=BODY_WIDTH,
        ).grid(row=row, column=0, sticky="w", pady=pady)

    def _build_language(self, body) -> None:
        self._heading(body, 0, "settings.interface_language", (0, 0))
        option_menu(
            body,
            self.controller.fonts,
            values=[locale["label"] for locale in locales.LOCALES],
            variable=self.language,
            command=self._on_selected,
        ).grid(row=1, column=0, sticky="w", pady=(8, 10))
        self._hint(body, 2, "settings.interface_hint", (0, 0))

    def _export_example_json(self) -> bool:
        return self._without_grab(
            lambda: self.controller.export_example_json(parent=self)
        )

    def _build_example_json(self, body) -> None:
        """Export the example plus a prompt that turns it into a real CV.

        The example JSON is not a demo file — it is the schema an LLM needs in
        order to convert a work history into something this app can import, so
        the prompt to hand it belongs right next to the button.
        """
        ctk.CTkFrame(body, height=1, fg_color=COLORS["border"]).grid(
            row=3, column=0, sticky="ew", pady=(22, 0)
        )
        self._heading(body, 4, "settings.example_json", (18, 0))
        self._hint(body, 5, "settings.example_json_hint", (6, 12))
        button(
            body,
            self.controller.fonts,
            text=self.t("settings.example_json_save"),
            command=self._export_example_json,
            variant="secondary",
            width=250,
        ).grid(row=6, column=0, sticky="w")

        self._hint(body, 7, "settings.example_json_prompt_hint", (18, 6))
        prompt = ctk.CTkTextbox(
            body,
            height=132,
            width=BODY_WIDTH,
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
            fg_color=COLORS["surface"],
            text_color=COLORS["text"],
            font=self.controller.fonts.small,
            wrap="word",
            activate_scrollbars=True,
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["muted"],
        )
        prompt.insert("1.0", self.t("settings.example_json_prompt"))
        prompt.configure(state="disabled")
        prompt.grid(row=8, column=0, sticky="ew")

        self.copy_button = button(
            body,
            self.controller.fonts,
            text=self.t("settings.copy_prompt"),
            command=self._copy_prompt,
            variant="secondary",
            width=250,
        )
        self.copy_button.grid(row=9, column=0, sticky="w", pady=(10, 0))

    def _copy_prompt(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(self.t("settings.example_json_prompt"))
        self.copy_button.configure(text=self.t("settings.prompt_copied"))
        self.after(1600, self._reset_copy_button)

    def _reset_copy_button(self) -> None:
        if self.copy_button.winfo_exists():
            self.copy_button.configure(text=self.t("settings.copy_prompt"))

    def _on_selected(self, label: str) -> None:
        for locale in locales.LOCALES:
            if locale["label"] == label:
                # Rebuilding the screens destroys and recreates every widget,
                # so close first rather than redrawing under our own feet.
                self.destroy()
                self.controller.set_ui_locale(locale["code"])
                return
