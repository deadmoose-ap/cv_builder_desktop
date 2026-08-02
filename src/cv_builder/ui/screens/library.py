"""Start screen: every CV stored on this device."""
from __future__ import annotations

from datetime import datetime

import customtkinter as ctk

from cv_builder.ui.components.fields import card
from cv_builder.ui.components.scrollable import AutoHideScrollableFrame
from cv_builder.ui.theme import COLORS, button


def format_modified_date(value: str, fallback: str) -> str:
    try:
        timestamp = datetime.fromisoformat(value)
        return timestamp.astimezone().strftime("%d %b %Y, %H:%M")
    except (TypeError, ValueError):
        return fallback


class LibraryScreen(ctk.CTkFrame):
    """Lists the CV library and its per-document actions."""

    def __init__(self, master, *, controller):
        super().__init__(master, corner_radius=0, fg_color=COLORS["background"])
        self.controller = controller
        self.fonts = controller.fonts
        self.t = controller.t
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_header()
        self._build_content()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, height=64, corner_radius=0, fg_color=COLORS["surface"])
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            header,
            text=self.t("app.name"),
            font=self.fonts.brand,
            text_color=COLORS["text"],
        ).grid(row=0, column=0, sticky="w", padx=(20, 0), pady=12)
        ctk.CTkLabel(
            header,
            text=self.t("library.subtitle"),
            font=self.fonts.small,
            text_color=COLORS["muted"],
        ).grid(row=0, column=1, sticky="w", padx=(18, 10))

        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.grid(row=0, column=2, sticky="e", padx=(0, 18), pady=11)
        # The only application-level settings entry point; the CV's own
        # language is chosen per document on the Preview step instead.
        gear = button(
            actions,
            self.fonts,
            text="⚙",
            command=self.controller.show_settings,
            variant="ghost",
            width=42,
            height=38,
        )
        gear.configure(font=self.fonts.gear)
        gear.pack(side="left", padx=(0, 6))
        button(
            actions,
            self.fonts,
            text=self.t("library.import_json"),
            command=self.controller.import_json,
            variant="secondary",
            width=96,
        ).pack(side="left", padx=(0, 8))
        button(
            actions,
            self.fonts,
            text=self.t("library.new_cv"),
            command=self.controller.create_cv,
            variant="primary",
            width=96,
        ).pack(side="left")

    def _build_content(self) -> None:
        content = ctk.CTkFrame(self, corner_radius=0, fg_color=COLORS["background"])
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(
            content,
            text=self.t("library.eyebrow"),
            font=self.fonts.small_bold,
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=44, pady=(34, 0))
        ctk.CTkLabel(
            content,
            text=self.t("library.title"),
            font=self.fonts.page_title,
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=44, pady=(5, 20))

        self.scroll = AutoHideScrollableFrame(
            content,
            corner_radius=0,
            fg_color="transparent",
            scrollbar_fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["muted"],
        )
        self.scroll.grid(row=2, column=0, sticky="nsew", padx=36, pady=(0, 32))
        self.scroll.grid_columnconfigure(0, weight=1)

    def refresh(self, records, preview) -> None:
        """Redraw the list. `preview(id)` returns (person, completion)."""
        for child in self.scroll.winfo_children():
            child.destroy()
        self.scroll.grid_columnconfigure(0, weight=1)

        if not records:
            self._render_empty_state()
            return

        for row, record in enumerate(records):
            self._render_card(row, record, *preview(record.id))
        self.scroll._schedule_scrollbar_check()

    def _render_empty_state(self) -> None:
        empty = card(self.scroll)
        empty.grid(row=0, column=0, sticky="ew", padx=(8, 16))
        empty.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            empty,
            text=self.t("library.empty_title"),
            font=self.fonts.card_title,
            text_color=COLORS["text"],
        ).grid(row=0, column=0, pady=(34, 5))
        ctk.CTkLabel(
            empty,
            text=self.t("library.empty_subtitle"),
            font=self.fonts.body,
            text_color=COLORS["muted"],
        ).grid(row=1, column=0)
        button(
            empty,
            self.fonts,
            text=self.t("library.empty_action"),
            command=self.controller.create_cv,
            variant="primary",
            width=112,
        ).grid(row=2, column=0, pady=(18, 34))
        self.scroll._schedule_scrollbar_check()

    def _render_card(self, row: int, record, person: str, completion: int) -> None:
        document_card = card(self.scroll)
        document_card.grid(row=row, column=0, sticky="ew", padx=(8, 16), pady=(0, 10))
        document_card.grid_columnconfigure(0, weight=1)
        details = ctk.CTkFrame(document_card, fg_color="transparent")
        details.grid(row=0, column=0, sticky="ew", padx=20, pady=17)
        details.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            details,
            text=record.title,
            font=self.fonts.card_title,
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            details,
            text=self.t("library.card_meta", person=person, percent=completion),
            font=self.fonts.body,
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))
        ctk.CTkLabel(
            details,
            text=self.t(
                "library.card_updated",
                date=format_modified_date(
                    record.updated_at, self.t("library.recently_updated")
                ),
            ),
            font=self.fonts.small,
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=2, column=0, sticky="w", pady=(4, 0))

        actions = ctk.CTkFrame(document_card, fg_color="transparent")
        actions.grid(row=0, column=1, sticky="e", padx=(8, 16))
        specs = (
            ("open", self.controller.open_library_document, "secondary", 62, (0, 4)),
            ("pdf", self.controller.export_document_pdf, "secondary", 52, (0, 4)),
            ("rename", self.controller.rename_cv, "ghost", 88, (0, 0)),
            ("duplicate", self.controller.duplicate_cv, "ghost", 88, (0, 0)),
            ("delete", self.controller.delete_cv, "danger", 72, (0, 0)),
        )
        for name, command, variant, width, padx in specs:
            button(
                actions,
                self.fonts,
                text=self.t(f"library.action.{name}"),
                command=lambda value=record.id, action=command: action(value),
                variant=variant,
                width=width,
                height=34,
            ).pack(side="left", padx=padx)
