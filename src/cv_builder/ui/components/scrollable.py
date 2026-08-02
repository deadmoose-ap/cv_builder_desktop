"""Scroll containers used by the screens."""
from __future__ import annotations

import tkinter as tk

import customtkinter as ctk


def touchpad_scroll_dy(event) -> int:
    """Vertical delta of a Tk 9 <TouchpadScroll> event.

    Since Tk 9.0 (TIP #684) macOS trackpad scrolling fires <TouchpadScroll>,
    not <MouseWheel>; its %D packs dx and dy as two signed 16-bit halves.
    """
    dy = event.delta & 0xFFFF
    if dy >= 0x8000:
        dy -= 0x10000
    return dy


class AutoHideScrollableFrame(ctk.CTkScrollableFrame):
    """CustomTkinter scroll frame that hides its bar when content fits.

    CTk's own mouse-wheel handling relies on a single ``bind_all`` callback
    that walks up each event widget's ``.master`` chain to guess which
    scrollable frame should react. With several scroll areas alive at once
    that guess regularly comes back wrong, so wheel/trackpad scrolling only
    ever appears to work when the scrollbar itself is grabbed directly. We
    bind the wheel handler straight onto this frame's own widgets instead,
    so scrolling never depends on that global guess.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._visibility_job: str | None = None
        self.bind("<Configure>", self._schedule_scrollbar_check, add="+")
        self._parent_canvas.bind(
            "<Configure>", self._schedule_scrollbar_check, add="+"
        )
        self._bind_mousewheel(self._parent_canvas)
        self._bind_mousewheel(self)
        self.after_idle(self._update_scrollbar_visibility)

    def _bind_mousewheel(self, widget) -> None:
        # Always recurse: children added after a widget was bound still need
        # their own bindings. Only the bind calls themselves are one-shot.
        if not getattr(widget, "_cv_wheel_bound", False):
            widget._cv_wheel_bound = True
            widget.bind("<MouseWheel>", self._on_mousewheel, add="+")
            widget.bind("<Button-4>", self._on_mousewheel, add="+")
            widget.bind("<Button-5>", self._on_mousewheel, add="+")
            try:
                widget.bind("<TouchpadScroll>", self._on_touchpad, add="+")
            except tk.TclError:
                pass  # Tk < 9 has no <TouchpadScroll>; trackpads send <MouseWheel>
        for child in widget.winfo_children():
            self._bind_mousewheel(child)

    def _on_mousewheel(self, event) -> None:
        if self._parent_canvas.yview() == (0.0, 1.0):
            return
        if event.num == 4:
            steps = -3
        elif event.num == 5:
            steps = 3
        else:
            steps = -event.delta
            if abs(steps) >= 120:
                steps = int(steps / 120) * 3
        self._parent_canvas.yview_scroll(int(steps), "units")

    def _on_touchpad(self, event) -> None:
        if self._parent_canvas.yview() == (0.0, 1.0):
            return
        dy = touchpad_scroll_dy(event)
        if dy:
            self._parent_canvas.yview_scroll(-dy, "units")

    def _schedule_scrollbar_check(self, _event=None):
        if self._visibility_job:
            self.after_cancel(self._visibility_job)
        self._visibility_job = self.after(40, self._update_scrollbar_visibility)

    def _update_scrollbar_visibility(self):
        self._visibility_job = None
        if not self.winfo_exists() or not self._parent_canvas.winfo_exists():
            return
        self._bind_mousewheel(self)
        bbox = self._parent_canvas.bbox(self._create_window_id)
        content_height = (bbox[3] - bbox[1]) if bbox else 0
        available_height = self._parent_canvas.winfo_height()
        needs_scrollbar = content_height > available_height + 2
        if needs_scrollbar:
            if not self._scrollbar.winfo_ismapped():
                self._scrollbar.grid()
        elif self._scrollbar.winfo_ismapped():
            self._scrollbar.grid_remove()
