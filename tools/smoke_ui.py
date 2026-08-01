"""Exercise the main UI states without entering the Tk event loop."""
from __future__ import annotations

from tempfile import TemporaryDirectory

from app import CVBuilderApp, SECTION_ORDER
from cv_library import CVLibrary
from cv_model import example_document


def main() -> None:
    temporary = TemporaryDirectory(prefix="cvbuilder-ui-smoke-")
    library = CVLibrary(temporary.name)
    record = library.create_document("Smoke Test CV", example_document())
    app = CVBuilderApp(library=library)
    states: list[tuple[str, int, int]] = []

    def exercise() -> None:
        app.update_idletasks()
        assert app.library_view.winfo_ismapped()
        assert app.skills_text.get("1.0", "end-1c") == ""
        assert app.summary_text.get("1.0", "end-1c") == ""
        app.editor_view.tkraise()
        app.show_section("profile")
        app.update_idletasks()
        name_entry = app.profile_entries["name"]
        assert name_entry._placeholder_label.winfo_ismapped()
        name_entry._focus_from_placeholder()
        name_entry._entry.insert(0, "Immediate typing")
        app.update_idletasks()
        assert app.profile_vars["name"].get() == "Immediate typing"
        app.profile_vars["name"].set("")
        app.show_library()

        app.open_library_document(record.id)
        app.update_idletasks()
        for section in SECTION_ORDER:
            app.show_section(section)
            app.update_idletasks()
            states.append(
                (
                    section,
                    app.section_frames[section].winfo_width(),
                    app.section_frames[section].winfo_height(),
                )
            )

        app.show_section("experience")
        app.edit_experience(0)
        app.update_idletasks()
        assert app.experience_editor_open
        app.cancel_experience_edit()
        app.update_idletasks()
        assert not app.experience_editor_open
        app.edit_experience(0)
        app.editor_vars["role"].set("UI SMOKE ROLE")
        app.save_experience_entry()
        app.update_idletasks()
        assert app.data["experience"][0]["role"] == "UI SMOKE ROLE"
        assert not app.experience_editor_open

        app.document_title_var.set("Renamed CV")
        app._commit_title_edit()
        app.update_idletasks()
        assert app.current_document_title == "Renamed CV"
        assert library.get_record(record.id).title == "Renamed CV"

        app.document_title_var.set("   ")
        app._commit_title_edit()
        app.update_idletasks()
        assert app.document_title_var.get() == "Renamed CV"
        assert library.get_record(record.id).title == "Renamed CV"

        app.duplicate_cv(record.id)
        app.update_idletasks()
        titles = {item.title for item in library.list_documents()}
        assert titles == {"Renamed CV", "Renamed CV copy"}
        app.after(800, finish)

    def finish() -> None:
        width, height = app.winfo_width(), app.winfo_height()
        assert width >= 900
        assert height >= 660
        assert all(
            section_width > 0 and section_height > 0
            for _, section_width, section_height in states
        )
        assert library.load_document(record.id)["experience"][0]["role"] == (
            "UI SMOKE ROLE"
        )
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
