"""Shared behaviour of the four editor sections."""
from __future__ import annotations

import tkinter as tk
from typing import Any, Callable

import customtkinter as ctk

from cv_builder.ui.theme import COLORS, Fonts


class Section(ctk.CTkFrame):
    """A page of the editor. Owns its widgets and its part of the document."""

    def __init__(
        self,
        master,
        *,
        fonts: Fonts,
        on_change: Callable[[], None],
        controller=None,
    ):
        super().__init__(master, corner_radius=0, fg_color=COLORS["background"])
        self.fonts = fonts
        self.on_change = on_change
        self.controller = controller
        self.grid_columnconfigure(0, weight=1)
        self.build()

    def build(self) -> None:
        """Create the widgets. Subclasses must implement."""
        raise NotImplementedError

    def tracked_var(self) -> tk.StringVar:
        """A StringVar that reports edits to the application."""
        variable = tk.StringVar()
        variable.trace_add("write", lambda *_args: self.on_change())
        return variable

    def collect(self, data: dict[str, Any]) -> None:
        """Write the widget values into the document."""

    def populate(self, data: dict[str, Any]) -> None:
        """Load the document into the widgets."""
