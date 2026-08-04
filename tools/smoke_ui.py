"""Exercise the main UI states without entering the Tk event loop."""
from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cv_builder.domain.model import example_document
from cv_builder.infrastructure.library import CVLibrary
from cv_builder.ui.app import CVBuilderApp
from cv_builder.ui.screens.editor import SECTION_ORDER


def main() -> None:
    temporary = TemporaryDirectory(prefix="cvbuilder-ui-smoke-")
    library = CVLibrary(temporary.name)
    record = library.create_document("Smoke Test CV", example_document())
    app = CVBuilderApp(library=library)
    editor = app.editor_view
    states: list[tuple[str, int, int]] = []

    def exercise() -> None:
        app.update_idletasks()
        assert app.library_view.winfo_ismapped()
        assert editor.profile.skills_text.get("1.0", "end-1c") == ""
        assert editor.summary.text.get("1.0", "end-1c") == ""
        editor.tkraise()
        app.show_section("profile")
        app.update_idletasks()
        name_entry = editor.profile.entries["name"]
        assert name_entry._placeholder_label.winfo_ismapped()
        name_entry._focus_from_placeholder()
        name_entry._entry.insert(0, "Immediate typing")
        app.update_idletasks()
        assert editor.profile.vars["name"].get() == "Immediate typing"
        editor.profile.vars["name"].set("")
        app.show_library()

        app.open_library_document(record.id)
        app.update_idletasks()
        for section in SECTION_ORDER:
            app.show_section(section)
            app.update_idletasks()
            frame = editor.sections[section]
            states.append((section, frame.winfo_width(), frame.winfo_height()))

        app.show_section("experience")
        experience = editor.experience
        experience.edit_entry(0)
        app.update_idletasks()
        assert experience.editor_open
        # Only the form being edited may be on screen: the two share a grid
        # cell, and the short company form does not cover the tall position one.
        assert experience.company_form.winfo_ismapped()
        assert not experience.position_form.winfo_ismapped()
        experience.cancel_edit()
        app.update_idletasks()
        assert not experience.editor_open
        experience.edit_position(0, 0)
        app.update_idletasks()
        assert experience.position_form.winfo_ismapped()
        assert not experience.company_form.winfo_ismapped()
        experience.role_var.set("UI SMOKE ROLE")
        experience.save_entry()
        app.update_idletasks()
        positions = app.data["experience"][0]["positions"]
        assert positions[0]["role"] == "UI SMOKE ROLE"
        assert positions[0]["start"], "the date picker kept the loaded start month"
        assert not experience.editor_open

        # A second position under the same company is what the schema is for.
        experience.add_position(0)
        experience.role_var.set("UI SMOKE EARLIER ROLE")
        experience.dates_field.set_value("2019-03", "2020-08", False)
        experience.save_entry()
        app.update_idletasks()
        assert len(app.data["experience"][0]["positions"]) == 3

        app.document_title_var.set("Renamed CV")
        app.commit_title_edit()
        app.update_idletasks()
        assert app.current_document_title == "Renamed CV"
        assert library.get_record(record.id).title == "Renamed CV"

        app.document_title_var.set("   ")
        app.commit_title_edit()
        app.update_idletasks()
        assert app.document_title_var.get() == "Renamed CV"
        assert library.get_record(record.id).title == "Renamed CV"

        app.duplicate_cv(record.id)
        app.update_idletasks()
        titles = {item.title for item in library.list_documents()}
        assert titles == {"Renamed CV", "Renamed CV copy"}

        app.show_section("preview")
        app.update_idletasks()
        preview = editor.preview
        assert app.current_section == "preview"
        assert preview.canvas.find_all()
        preview.select_theme("mint")
        app.update_idletasks()
        assert app.data["theme"] == "mint"
        assert preview.selected_theme == "mint"

        # The CV's language and the interface language switch independently.
        preview.select_locale("ja")
        app.update_idletasks()
        assert app.data["locale"] == "ja"
        assert app.settings.ui_locale == "en"

        app.set_ui_locale("ru")
        app.update_idletasks()
        assert app.settings.ui_locale == "ru"
        assert app.t("editor.all_cvs") == "Все резюме"
        assert app.editor_view.profile.entries["name"].placeholder_text == "ВАШЕ ИМЯ"
        assert app.data["locale"] == "ja", "the CV keeps its own language"
        app.set_ui_locale("en")
        app.update_idletasks()

        app.show_section("profile")
        app.update_idletasks()
        app.after(800, finish)

    def finish() -> None:
        width, height = app.winfo_width(), app.winfo_height()
        assert width >= 900
        assert height >= 660
        assert all(
            section_width > 0 and section_height > 0
            for _, section_width, section_height in states
        )
        stored = library.load_document(record.id)
        assert stored["experience"][0]["positions"][0]["role"] == "UI SMOKE ROLE"
        assert stored["theme"] == "mint"
        assert stored["locale"] == "ja"
        print(f"window={width}x{height}")
        print(
            f"library={app.library_view.winfo_width()}x"
            f"{app.library_view.winfo_height()}"
        )
        for section, section_width, section_height in states:
            print(f"{section}={section_width}x{section_height}")
        app.destroy()

    app.after(150, exercise)
    app.mainloop()
    temporary.cleanup()


if __name__ == "__main__":
    main()
