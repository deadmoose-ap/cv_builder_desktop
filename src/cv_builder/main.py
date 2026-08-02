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
        from cv_builder.exporters.pdf import generate_pdf

        generate_pdf(
            new_document(),
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
