"""Application shell: composition, navigation and document lifecycle.

The screens own their widgets, the service owns storage and export. This class
holds the open document, routes commands between the two, and owns nothing else.
"""
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from cv_builder.application.document_service import DocumentService
from cv_builder.domain.completion import calculate_completion
from cv_builder.infrastructure.library import CVLibrary
from cv_builder.infrastructure.settings import SettingsStore
from cv_builder.ui.i18n import Translator, placeholders
from cv_builder.ui.screens.editor import SECTION_ORDER, EditorScreen
from cv_builder.ui.screens.library import LibraryScreen
from cv_builder.ui.screens.settings_dialog import SettingsDialog
from cv_builder.ui.theme import COLORS, Fonts


# The product name is a brand, identical in every locale; the interface copy
# under "app.name" carries the same value for the in-window wordmark.
APP_NAME = "CV Builder"
AUTOSAVE_DELAY_MS = 650

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class CVBuilderApp(ctk.CTk):
    """Root window. Owns the open document and the navigation between screens."""

    def __init__(
        self,
        library: CVLibrary | None = None,
        *,
        show_library_on_start: bool = True,
        service: DocumentService | None = None,
        settings: SettingsStore | None = None,
    ):
        super().__init__(fg_color=COLORS["background"])
        self.title(APP_NAME)
        self.geometry("1120x780")
        self.minsize(940, 680)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.service = service or DocumentService(library)
        # Settings live beside the library so a test or smoke run pointed at a
        # temporary directory never touches the real preferences file.
        self.settings_store = settings or SettingsStore(self.service.library.root)
        self.settings = self.settings_store.load()
        self.t = Translator(self.settings.ui_locale)
        self.placeholders = placeholders(self.settings.ui_locale)
        self.data = self.service.new_document()
        self.current_document_id: str | None = None
        self.current_document_title = ""
        self.current_section = "profile"
        self._loading = True
        self._progress_job: str | None = None
        self._autosave_job: str | None = None
        self._title_commit_in_progress = False

        self.status = tk.StringVar(value=self.t("status.library"))
        self.document_title_var = tk.StringVar(value="")
        self.progress_text = tk.StringVar(value=self.t("status.progress", percent=0))

        self.fonts = Fonts(self.settings.ui_locale)
        self._build_screens()

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

    # --- convenience -----------------------------------------------------

    @property
    def library(self) -> CVLibrary:
        return self.service.library

    def _build_screens(self) -> None:
        self.editor_view = EditorScreen(self, controller=self)
        self.library_view = LibraryScreen(self, controller=self)
        for view in (self.editor_view, self.library_view):
            view.grid(row=0, column=0, sticky="nsew")

    # --- interface language ----------------------------------------------

    def show_settings(self) -> None:
        SettingsDialog(self, controller=self)

    def set_ui_locale(self, code: str) -> None:
        """Switch the interface language and rebuild both screens.

        Rebuilding beats keeping a StringVar per label: the document lives in
        `self.data`, not in the widgets, so throwing the widgets away and
        recreating them loses nothing and keeps every call site a plain string.
        """
        if code == self.settings.ui_locale:
            return
        self._save_now()
        self.settings = self.settings_store.set_ui_locale(code)
        self.t = Translator(code)
        self.placeholders = placeholders(code)
        self.fonts = Fonts(code)
        self.title(self.t("app.name"))

        section, document_id = self.current_section, self.current_document_id
        showing_library = self.library_view.winfo_ismapped()
        self.editor_view.destroy()
        self.library_view.destroy()
        self._build_screens()

        self.status.set(self.t("status.saved" if document_id else "status.library"))
        self.populate_form()
        self.editor_view.set_title_editable(document_id is not None)
        self.show_section(section)
        if showing_library:
            self.show_library()
        else:
            self.editor_view.tkraise()

    def _bind_shortcuts(self) -> None:
        self.bind_all("<Control-s>", lambda _event: self.save_file())
        self.bind_all("<Command-s>", lambda _event: self.save_file())
        self.bind_all("<Control-o>", lambda _event: self.show_library())
        self.bind_all("<Command-o>", lambda _event: self.show_library())
        self.bind_all("<Escape>", self._handle_escape)

    def _handle_escape(self, _event=None):
        experience = self.editor_view.experience
        if self.current_section == "experience" and experience.editor_open:
            experience.cancel_edit()

    # --- navigation ------------------------------------------------------

    def show_section(self, section: str) -> None:
        if section not in SECTION_ORDER:
            raise ValueError(f"Unknown section: {section}")
        self.current_section = section
        self.editor_view.show_section(section)
        if section == "preview":
            # Rendered after raising, so the canvas knows its real size.
            self.editor_view.preview.render_document(self.collect_form())

    def show_library(self) -> None:
        self._save_now()
        self.refresh_library()
        self.library_view.tkraise()
        self.editor_view.set_title_editable(False)
        self.status.set(self.t("status.library"))

    def show_preview(self) -> None:
        """Jump to the final step."""
        self.show_section("preview")

    def apply_preview_theme(self, theme_key: str) -> None:
        """Choose the sidebar colour from outside the preview step."""
        self.editor_view.preview.select_theme(theme_key)

    # --- library commands ------------------------------------------------

    def refresh_library(self) -> None:
        try:
            records = self.service.list_documents()
        except Exception as error:
            records = []
            messagebox.showerror(
                self.t("error.library_open"), str(error), parent=self
            )
        self.library_view.refresh(records, self._document_preview)

    def _document_preview(self, document_id: str) -> tuple[str, int]:
        try:
            document = self.service.load(document_id)
        except Exception:
            return self.t("library.preview_failed"), 0
        return (
            document["profile"].get("name") or self.t("library.no_name"),
            calculate_completion(document),
        )

    def create_cv(self) -> None:
        try:
            record = self.service.create(locale=self.settings.ui_locale)
        except Exception as error:
            messagebox.showerror(self.t("error.create"), str(error), parent=self)
            return
        self.open_library_document(record.id)

    def open_library_document(self, document_id: str) -> None:
        self._cancel_autosave()
        try:
            record = self.service.get_record(document_id)
            self.data = self.service.load(document_id)
        except Exception as error:
            messagebox.showerror(self.t("error.open"), str(error), parent=self)
            return
        self.current_document_id = record.id
        self.current_document_title = record.title
        self.editor_view.set_title_editable(True)
        self.document_title_var.set(record.title)
        self.populate_form()
        self.show_section("profile")
        self.editor_view.tkraise()
        self.status.set(self.t("status.saved"))

    def rename_cv(self, document_id: str) -> None:
        try:
            self.service.get_record(document_id)
        except Exception as error:
            messagebox.showerror(self.t("error.rename"), str(error), parent=self)
            return
        dialog = ctk.CTkInputDialog(
            text=self.t("dialog.rename.text"),
            title=self.t("dialog.rename.title"),
        )
        value = dialog.get_input()
        if value is None:
            return
        self._apply_rename(document_id, value)
        self.refresh_library()

    def _apply_rename(self, document_id: str, value: str) -> bool:
        """Persist a new title and keep the editor header in sync."""
        try:
            updated = self.service.rename(document_id, value)
        except Exception as error:
            messagebox.showerror(self.t("error.rename"), str(error), parent=self)
            self.reset_title_field()
            return False
        if self.current_document_id == document_id:
            self.current_document_title = updated.title
            self.document_title_var.set(updated.title)
        return True

    def reset_title_field(self) -> None:
        self.document_title_var.set(self.current_document_title)

    def commit_title_edit(self, *_args) -> None:
        """Apply the header title field; revert when empty or unchanged."""
        if self._title_commit_in_progress:
            return
        if self.current_document_id is None:
            self.reset_title_field()
            return
        value = self.document_title_var.get().strip()
        if not value or value == self.current_document_title:
            self.reset_title_field()
            return
        self._title_commit_in_progress = True
        try:
            self._apply_rename(self.current_document_id, value)
        finally:
            self._title_commit_in_progress = False

    def duplicate_cv(self, document_id: str) -> None:
        try:
            self.service.duplicate(document_id)
        except Exception as error:
            messagebox.showerror(self.t("error.duplicate"), str(error), parent=self)
            return
        self.refresh_library()

    def delete_cv(self, document_id: str) -> None:
        try:
            record = self.service.get_record(document_id)
        except Exception:
            self.refresh_library()
            return
        if not messagebox.askyesno(
            self.t("dialog.delete.title"),
            self.t("dialog.delete.message", title=record.title),
            detail=self.t("dialog.delete.detail"),
            parent=self,
        ):
            return
        try:
            self.service.delete(document_id)
        except Exception as error:
            messagebox.showerror(self.t("error.delete"), str(error), parent=self)
            return
        if self.current_document_id == document_id:
            self.current_document_id = None
            self.current_document_title = ""
            self.document_title_var.set("")
            self.data = self.service.new_document()
        self.refresh_library()

    # --- import / export -------------------------------------------------

    def import_json(self) -> None:
        path = filedialog.askopenfilename(
            title=self.t("dialog.import.title"),
            filetypes=[
                (self.t("filetype.json"), "*.json"),
                (self.t("filetype.all"), "*.*"),
            ],
        )
        if not path:
            return
        try:
            record = self.service.import_json(path)
        except Exception as error:
            messagebox.showerror(self.t("error.import"), str(error), parent=self)
            return
        self.open_library_document(record.id)

    def export_example_json(self) -> bool:
        path = filedialog.asksaveasfilename(
            title=self.t("dialog.example.title"),
            defaultextension=".json",
            initialfile=self.t("file.example_json"),
            filetypes=[(self.t("filetype.json"), "*.json")],
        )
        if not path:
            return False
        try:
            self.service.export_example_json(path)
            messagebox.showinfo(
                self.t("dialog.example_saved.title"),
                self.t("dialog.example_saved.message", path=path),
                parent=self,
            )
            return True
        except Exception as error:
            messagebox.showerror(self.t("error.example"), str(error), parent=self)
            return False

    def export_current_json(self) -> bool:
        if self.current_document_id is None:
            return False
        suggested = self.current_document_title.strip().replace("/", "-") or self.t(
            "file.default_cv"
        )
        path = filedialog.asksaveasfilename(
            title=self.t("dialog.export_json.title"),
            defaultextension=".json",
            initialfile=f"{suggested}.json",
            filetypes=[(self.t("filetype.json"), "*.json")],
        )
        if not path:
            return False
        try:
            self._save_now()
            self.service.export_json(path, self.collect_form())
            self.status.set(self.t("status.json_exported"))
            return True
        except Exception as error:
            messagebox.showerror(self.t("error.export_json"), str(error), parent=self)
            return False

    def generate(self) -> bool:
        return self._export_pdf(self.collect_form())

    def export_document_pdf(self, document_id: str) -> bool:
        """Export any CV from the library without opening it in the editor."""
        if document_id == self.current_document_id:
            self._save_now()
            return self._export_pdf(self.collect_form())
        try:
            data = self.service.load(document_id)
        except Exception as error:
            messagebox.showerror(self.t("error.pdf"), str(error), parent=self)
            return False
        return self._export_pdf(data)

    def _export_pdf(self, data: dict) -> bool:
        name = str(data.get("profile", {}).get("name") or "").strip()
        if not name:
            messagebox.showwarning(
                self.t("dialog.missing_name.title"),
                self.t("dialog.missing_name.message"),
                parent=self,
            )
            return False
        path = filedialog.asksaveasfilename(
            title=self.t("dialog.export_pdf.title"),
            defaultextension=".pdf",
            initialfile=self.t("file.pdf_name", name=name),
            filetypes=[(self.t("filetype.pdf"), "*.pdf")],
        )
        if not path:
            return False
        try:
            self.status.set(self.t("status.exporting_pdf"))
            self.update_idletasks()
            self.service.export_pdf(path, data)
            self.status.set(self.t("status.exported", name=Path(path).name))
            messagebox.showinfo(
                self.t("dialog.pdf_created.title"),
                self.t("dialog.pdf_created.message", path=path),
                parent=self,
            )
            return True
        except Exception as error:
            self.status.set(self.t("status.pdf_failed"))
            messagebox.showerror(self.t("error.pdf"), str(error), parent=self)
            return False

    # --- document state --------------------------------------------------

    def collect_form(self) -> dict:
        return self.editor_view.collect(self.data)

    def populate_form(self) -> None:
        self._loading = True
        self.editor_view.populate(self.data)
        self._loading = False
        self._update_progress()

    def on_form_changed(self) -> None:
        """A section reported an edit."""
        if not self._loading:
            self._mark_dirty()

    def _mark_dirty(self) -> None:
        if self.current_document_id is None:
            return
        self.status.set(self.t("status.saving"))
        self._schedule_progress_update()
        self._schedule_autosave()

    def _schedule_autosave(self) -> None:
        self._cancel_autosave()
        self._autosave_job = self.after(AUTOSAVE_DELAY_MS, self._save_now)

    def _cancel_autosave(self) -> None:
        if self._autosave_job:
            try:
                self.after_cancel(self._autosave_job)
            except tk.TclError:
                pass
            self._autosave_job = None

    def _save_now(self) -> bool:
        self._cancel_autosave()
        if self.current_document_id is None:
            return False
        try:
            self.service.save(self.current_document_id, self.collect_form())
            self.status.set(self.t("status.saved"))
            return True
        except Exception:
            self.status.set(self.t("status.save_failed"))
            return False

    def _close_application(self) -> None:
        self._save_now()
        self.destroy()

    def _schedule_progress_update(self) -> None:
        if self._progress_job:
            self.after_cancel(self._progress_job)
        self._progress_job = self.after(80, self._update_progress)

    def _update_progress(self) -> None:
        self._progress_job = None
        percent = calculate_completion(self.collect_form())
        self.editor_view.set_progress(percent)
        self.progress_text.set(self.t("status.progress", percent=percent))

    # --- menu-style aliases ----------------------------------------------

    def new_file(self) -> None:
        self.create_cv()

    def open_file(self) -> None:
        self.import_json()

    def save_file(self) -> bool:
        return self._save_now()

    def save_as(self) -> bool:
        return self.export_current_json()
