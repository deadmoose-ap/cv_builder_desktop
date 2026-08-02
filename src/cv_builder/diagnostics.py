"""Headless checks that must also run inside the frozen application."""
from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory

from cv_builder.domain.model import example_document
from cv_builder.infrastructure.library import CVLibrary
from cv_builder.ui.app import CVBuilderApp
from cv_builder.ui.screens.editor import SECTION_ORDER


def run_packaged_ui_smoke(output: Path) -> None:
    """Exercise frozen UI layout and persist diagnostics without user input."""
    temporary = TemporaryDirectory(prefix="cvbuilder-packaged-smoke-")
    library = CVLibrary(temporary.name)
    record = library.create_document("Packaged Smoke CV", example_document())
    app = CVBuilderApp(library=library)

    def exercise() -> None:
        app.update_idletasks()
        profile = app.editor_view.profile
        placeholders_are_data = any(
            (
                profile.vars["name"].get(),
                profile.skills_text.get("1.0", "end-1c"),
                app.editor_view.summary.text.get("1.0", "end-1c"),
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
            frame = app.editor_view.sections[section]
            sections[section] = {
                "width": frame.winfo_width(),
                "height": frame.winfo_height(),
            }
        app.show_section("experience")
        app.editor_view.experience.edit_entry(0)
        app.update_idletasks()
        app.show_section("preview")
        app.update_idletasks()
        preview_items = len(app.editor_view.preview.canvas.find_all())
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
            "experience_editor_open": app.editor_view.experience.editor_open,
            "preview_canvas_items": preview_items,
        }
        output.write_text(json.dumps(result, indent=2), encoding="utf-8")
        app.destroy()

    app.after(180, exercise)
    app.mainloop()
    temporary.cleanup()
