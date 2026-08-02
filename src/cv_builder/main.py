"""Entry point for the desktop application and its packaged smoke checks."""
from __future__ import annotations

import sys
from pathlib import Path


def _argument_path(flag: str, fallback: str) -> Path:
    index = sys.argv.index(flag)
    if len(sys.argv) > index + 1:
        return Path(sys.argv[index + 1])
    return Path.cwd() / fallback


def main() -> None:
    if "--ui-smoke-test" in sys.argv:
        from cv_builder.diagnostics import run_packaged_ui_smoke

        run_packaged_ui_smoke(
            _argument_path("--ui-smoke-test", "CVBuilder-ui-smoke.json")
        )
        return
    if "--smoke-test" in sys.argv:
        from cv_builder.domain.model import new_document
        from cv_builder.exporters.pdf import font_for_locale, generate_pdf, register_fonts

        document = new_document()
        if "--locale" in sys.argv:
            # Proves the bundled CJK face actually shipped: registering falls
            # back to the Latin font when the file is missing from the build,
            # so a mismatch here fails the packaged check instead of silently
            # exporting blank boxes on a machine without a system CJK font.
            locale = sys.argv[sys.argv.index("--locale") + 1]
            document["locale"] = locale
            resolved = register_fonts(locale)
            if resolved != font_for_locale(locale):
                raise SystemExit(
                    f"No font for locale {locale}: fell back to {resolved}"
                )
            print(f"font for {locale}: {resolved}")
        generate_pdf(
            document,
            _argument_path("--smoke-test", "CVBuilder-smoke-test.pdf"),
        )
        return

    from cv_builder.ui.app import CVBuilderApp

    CVBuilderApp().mainloop()


if __name__ == "__main__":
    if __package__ in (None, ""):
        # Running the file directly (PyInstaller entry point, `python main.py`).
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    main()
