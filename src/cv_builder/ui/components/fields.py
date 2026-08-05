"""Form widgets and the card/field factories shared by the editor sections."""
from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from cv_builder.ui.theme import COLORS, Fonts, button


# One dropdown height across the app (design spec §5.3).
MENU_HEIGHT = 34


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


def card(parent, **kwargs) -> ctk.CTkFrame:
    """A white rounded surface with a hairline border."""
    return ctk.CTkFrame(
        parent,
        corner_radius=13,
        fg_color=COLORS["surface"],
        border_width=1,
        border_color=COLORS["border"],
        **kwargs,
    )


def option_menu(
    parent,
    fonts: Fonts,
    *,
    values: list[str],
    variable: tk.StringVar,
    command=None,
    width: int = 250,
    height: int = MENU_HEIGHT,
    fg_color: str | None = None,
) -> ctk.CTkOptionMenu:
    """The one dropdown look this app uses, everywhere it uses one.

    The default height is the spec's 34 px (design spec §5.3): the CV-language
    selector and the experience date pickers must read as one component, so a
    new dropdown should take the default rather than pick its own number.

    `fg_color` defaults to the surface white that reads against the editor
    background; pass `surface_alt` when the menu sits on a white card, where
    white on white would leave only the arrow visible.

    Width is always fixed — never grid this with `sticky="ew"`. CTkOptionMenu
    draws its arrow at the configured width, not the allocated one.
    """
    return ctk.CTkOptionMenu(
        parent,
        values=values,
        variable=variable,
        command=command,
        width=width,
        height=height,
        corner_radius=8,
        font=fonts.body,
        dropdown_font=fonts.body,
        fg_color=fg_color or COLORS["surface"],
        button_color=COLORS["border"],
        button_hover_color=COLORS["muted"],
        text_color=COLORS["text"],
        dropdown_fg_color=COLORS["surface"],
        dropdown_text_color=COLORS["text"],
        dropdown_hover_color=COLORS["selection"],
    )


def checkbox(parent, fonts: Fonts, *, text: str, variable, command=None) -> ctk.CTkCheckBox:
    """A checkbox in the Calm Workspace palette."""
    return ctk.CTkCheckBox(
        parent,
        text=text,
        variable=variable,
        command=command,
        font=fonts.body,
        text_color=COLORS["text"],
        fg_color=COLORS["accent"],
        hover_color=COLORS["accent_hover"],
        border_color=COLORS["border"],
        border_width=1,
        corner_radius=5,
        checkbox_width=20,
        checkbox_height=20,
    )


def textbox(parent, fonts: Fonts, *, height: int, placeholder: str = "") -> PlaceholderTextbox:
    return PlaceholderTextbox(
        parent,
        height=height,
        placeholder_text=placeholder,
        corner_radius=8,
        border_width=1,
        border_color=COLORS["border"],
        fg_color=COLORS["surface"],
        text_color=COLORS["text"],
        font=fonts.body,
        wrap="word",
        undo=True,
        scrollbar_button_color=COLORS["border"],
        scrollbar_button_hover_color=COLORS["muted"],
    )


def form_field(
    parent,
    fonts: Fonts,
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
    """A labelled single-line field, gridded into `parent`."""
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
        font=fonts.label,
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
        font=fonts.body,
    )
    entry.grid(row=1, column=0, sticky="ew")
    return entry


def section_header(
    parent,
    fonts: Fonts,
    *,
    step: str,
    title: str | tk.StringVar,
    subtitle: str | tk.StringVar,
    action_text: str | None = None,
    action_command=None,
) -> ctk.CTkButton | None:
    """Step label, page title, subtitle and an optional primary action."""
    header = ctk.CTkFrame(parent, fg_color="transparent")
    header.grid(row=0, column=0, sticky="ew", padx=36, pady=(27, 18))
    header.grid_columnconfigure(0, weight=1)
    ctk.CTkLabel(
        header,
        text=step.upper(),
        font=fonts.small_bold,
        text_color=COLORS["muted"],
        anchor="w",
    ).grid(row=0, column=0, sticky="w")
    title_options = (
        {"textvariable": title} if isinstance(title, tk.StringVar) else {"text": title}
    )
    ctk.CTkLabel(
        header,
        font=fonts.page_title,
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
        font=fonts.body,
        text_color=COLORS["muted"],
        anchor="w",
        **subtitle_options,
    ).grid(row=2, column=0, sticky="w")
    if action_text:
        action = button(
            header,
            fonts,
            text=action_text,
            command=action_command,
            variant="primary",
            width=120,
        )
        action.grid(row=0, column=1, rowspan=3, sticky="e")
        return action
    return None
