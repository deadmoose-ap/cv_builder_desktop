"""Capture the real CV Builder UI as PNG files on macOS.

The app's own Cocoa content view is rendered directly, so Screen Recording
permission is not required. The files in ``ui-screens`` are implementation
regression assets; HTML design targets are stored separately in
``ui-reference``.
"""
from __future__ import annotations

import ctypes
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cv_builder.domain.model import example_document
from cv_builder.infrastructure.library import CVLibrary
from cv_builder.ui.app import CVBuilderApp


class NSPoint(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]


class NSSize(ctypes.Structure):
    _fields_ = [("width", ctypes.c_double), ("height", ctypes.c_double)]


class NSRect(ctypes.Structure):
    _fields_ = [("origin", NSPoint), ("size", NSSize)]


OBJC = ctypes.cdll.LoadLibrary("/usr/lib/libobjc.A.dylib")
OBJC.objc_getClass.argtypes = [ctypes.c_char_p]
OBJC.objc_getClass.restype = ctypes.c_void_p
OBJC.sel_registerName.argtypes = [ctypes.c_char_p]
OBJC.sel_registerName.restype = ctypes.c_void_p
MESSAGE = OBJC.objc_msgSend


def message(receiver, selector, restype=ctypes.c_void_p, *args):
    """Send one typed Objective-C message."""
    MESSAGE.restype = restype
    MESSAGE.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        *[type(value) for value in args],
    ]
    return MESSAGE(
        receiver,
        OBJC.sel_registerName(selector.encode("utf-8")),
        *args,
    )


def capture_main_window(destination: Path) -> None:
    """Write the current main window content as a Retina-aware PNG."""
    app_class = OBJC.objc_getClass(b"NSApplication")
    cocoa_app = message(app_class, "sharedApplication")
    window = message(cocoa_app, "mainWindow")
    if not window:
        window = message(cocoa_app, "keyWindow")
    if not window:
        raise RuntimeError("No active macOS window was found.")

    view = message(window, "contentView")
    bounds = message(view, "bounds", NSRect)
    bitmap = message(
        view,
        "bitmapImageRepForCachingDisplayInRect:",
        ctypes.c_void_p,
        bounds,
    )
    message(
        view,
        "cacheDisplayInRect:toBitmapImageRep:",
        None,
        bounds,
        ctypes.c_void_p(bitmap),
    )
    data = message(
        bitmap,
        "representationUsingType:properties:",
        ctypes.c_void_p,
        ctypes.c_ulong(4),  # NSBitmapImageFileTypePNG
        ctypes.c_void_p(0),
    )
    string_class = OBJC.objc_getClass(b"NSString")
    path_string = message(
        string_class,
        "stringWithUTF8String:",
        ctypes.c_void_p,
        ctypes.c_char_p(str(destination).encode("utf-8")),
    )
    written = message(
        data,
        "writeToFile:atomically:",
        ctypes.c_bool,
        ctypes.c_void_p(path_string),
        ctypes.c_bool(True),
    )
    if not written:
        raise RuntimeError(f"Could not write {destination}")


def main() -> None:
    if sys.platform != "darwin":
        raise SystemExit("This capture helper only runs on macOS.")

    output = PROJECT_ROOT / "ui-screens"
    output.mkdir(exist_ok=True)
    temporary = TemporaryDirectory(prefix="cvbuilder-screen-capture-")
    library = CVLibrary(temporary.name)
    record = library.create_document("Product Designer CV")
    app = CVBuilderApp(library=library)
    app.geometry("1120x780")
    app.deiconify()
    app.lift()
    app.focus_force()

    states = [
        ("library", "00-library"),
        ("profile", "01-profile"),
        ("summary", "02-summary"),
        ("experience", "03-experience"),
        ("education", "04-education"),
        ("experience-editor", "05-experience-editor"),
        ("preview", "06-preview"),
    ]
    position = 0

    def prepare_next() -> None:
        nonlocal position
        if position >= len(states):
            app.destroy()
            return

        state, _ = states[position]
        if state == "library":
            app.show_library()
        elif state == "experience-editor":
            app.show_section("experience")
            # The position form is the interesting one: dates, checkbox, lists.
            experience = app.editor_view.experience
            if not experience.entries:
                experience.company_var.set("Company")
                experience._save_company(None)
            else:
                experience.add_position(0)
        elif state == "preview":
            # A filled document shows the real preview layout, not empty pages.
            sample = library.create_document("Preview Sample CV", example_document())
            app.open_library_document(sample.id)
            app.show_section("preview")
        else:
            if app.current_document_id is None:
                app.open_library_document(record.id)
            app.show_section(state)
        app.update_idletasks()
        app.after(180, capture_current)

    def capture_current() -> None:
        nonlocal position
        _, name = states[position]
        capture_main_window(output / f"{name}.png")
        position += 1
        app.after(100, prepare_next)

    app.after(500, prepare_next)
    app.mainloop()
    temporary.cleanup()


if __name__ == "__main__":
    main()
