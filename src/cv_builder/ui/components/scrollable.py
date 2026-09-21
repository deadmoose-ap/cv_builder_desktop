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
        # TouchpadScroll reports pixel deltas; keep canvas units pixel-sized
        # so the existing -dy conversion remains smooth and predictable.
        self._parent_canvas.configure(yscrollincrement=8)
        self.bind("<Configure>", self._schedule_scrollbar_check, add="+")
        self._parent_canvas.bind(
            "<Configure>", self._schedule_scrollbar_check, add="+"
        )
        self._bind_mousewheel(self._parent_canvas)
        self._bind_mousewheel(self)
        self.after_idle(self._update_scrollbar_visibility)

    def _bind_mousewheel(self, widget) -> None:
        # CTkTextbox contains a real tk.Text child.  Binding the outer-frame
        # callback to that child makes one wheel event move both the text and
        # the form.  Give the text its own arbitration callback instead: it
        # consumes the event while it can move, and hands it to the canvas at
        # its top/bottom boundary.
        if isinstance(widget, ctk.CTkTextbox):
            self._bind_text_mousewheel(widget._textbox)
            return
        if isinstance(widget, tk.Text):
            self._bind_text_mousewheel(widget)
            return
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

    def _bind_text_mousewheel(self, widget: tk.Text) -> None:
        if getattr(widget, "_cv_inner_wheel_bound", False):
            return
        widget.bind("<MouseWheel>", self._on_text_mousewheel, add="+")
        widget.bind("<Button-4>", self._on_text_mousewheel, add="+")
        widget.bind("<Button-5>", self._on_text_mousewheel, add="+")
        try:
            widget.bind("<TouchpadScroll>", self._on_text_touchpad, add="+")
        except tk.TclError:
            pass  # Tk < 9 has no <TouchpadScroll>; trackpads send <MouseWheel>
        # Set the marker only after the required bindings are installed.  Tk 9
        # Text does not expose Canvas' yscrollincrement option.
        widget._cv_inner_wheel_bound = True

    @staticmethod
    def _mousewheel_steps(event) -> int:
        if event.num == 4:
            return -3
        if event.num == 5:
            return 3
        steps = -event.delta
        if abs(steps) >= 120:
            steps = int(steps / 120) * 3
        return int(steps)

    @staticmethod
    def _target_can_scroll(target, steps: int) -> bool:
        first, last = target.yview()
        if first <= 0.0 and steps < 0:
            return False
        if last >= 1.0 and steps > 0:
            return False
        return (last - first) < 1.0

    def _scroll_canvas(self, steps: int) -> None:
        if steps and self._target_can_scroll(self._parent_canvas, steps):
            self._parent_canvas.yview_scroll(steps, "units")

    def _scroll_text_or_canvas(self, widget: tk.Text, steps: int) -> None:
        if steps and self._target_can_scroll(widget, steps):
            widget.yview_scroll(steps, "units")
        else:
            self._scroll_canvas(steps)

    def _on_mousewheel(self, event) -> str:
        self._scroll_canvas(self._mousewheel_steps(event))
        return "break"

    def _on_text_mousewheel(self, event) -> str:
        self._scroll_text_or_canvas(event.widget, self._mousewheel_steps(event))
        return "break"

    def _on_touchpad(self, event) -> str:
        dy = touchpad_scroll_dy(event)
        if dy:
            self._scroll_canvas(-dy)
        return "break"

    def _on_text_touchpad(self, event) -> str:
        dy = touchpad_scroll_dy(event)
        if dy:
            # Text scrolls in line units; Tk 9 reports trackpad deltas in
            # pixels.  Keep the same approximate 8 px unit used by the canvas.
            steps = int(round(-dy / 8)) or (-1 if dy > 0 else 1)
            self._scroll_text_or_canvas(event.widget, steps)
        return "break"

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
