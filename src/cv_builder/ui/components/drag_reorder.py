"""Drag-and-drop reordering for rows gridded in a single column."""
from __future__ import annotations

import tkinter as tk
from typing import Callable

# Pointer travel before a press turns into a drag, so a plain click on a
# card never moves it.
DRAG_THRESHOLD = 5
# Distance from the viewport edge where a drag starts scrolling the list.
EDGE_ZONE = 48
AUTOSCROLL_MS = 30


class DragReorder:
    """Move gridded rows by dragging them; the new order is reported on drop.

    Rows keep their own grid options — only the `row` index changes, live,
    while the pointer moves, so the list itself shows where the row will land.
    `canvas` is the scroll canvas that hosts the container, if any: dragging
    near its top or bottom edge scrolls it.
    """

    def __init__(
        self,
        *,
        on_drop: Callable[[list[str]], None],
        on_drag_state: Callable[[tk.Misc, bool], None] | None = None,
        canvas: tk.Canvas | None = None,
    ):
        self.on_drop = on_drop
        self.on_drag_state = on_drag_state
        self.canvas = canvas
        self.rows: list[tuple[str, tk.Misc]] = []
        self._press_y: int | None = None
        self._pending: tuple[str, tk.Misc] | None = None
        self._dragged: tuple[str, tk.Misc] | None = None
        self._start_order: list[str] = []
        self._pointer_y = 0
        self._scroll_job: str | None = None

    def add(self, key: str, row: tk.Misc, handles: list[tk.Misc]) -> None:
        item = (key, row)
        self.rows.append(item)
        for handle in handles:
            handle.bind(
                "<ButtonPress-1>",
                lambda event, item=item: self._press(event, item),
                add="+",
            )
            handle.bind("<B1-Motion>", self._motion, add="+")
            handle.bind("<ButtonRelease-1>", self._release, add="+")

    def order(self) -> list[str]:
        return [key for key, _row in self.rows]

    # --- pointer ---------------------------------------------------------

    def _press(self, event, item) -> None:
        self._press_y = event.y_root
        self._pending = item

    def _motion(self, event) -> None:
        if self._press_y is None:
            return
        self._pointer_y = event.y_root
        if self._dragged is None:
            if abs(event.y_root - self._press_y) < DRAG_THRESHOLD:
                return
            self._dragged = self._pending
            self._start_order = self.order()
            if self.on_drag_state:
                self.on_drag_state(self._dragged[1], True)
            self._autoscroll()
        self._follow_pointer()

    def _release(self, _event) -> None:
        self._press_y = None
        if self._dragged is None:
            return
        dragged, self._dragged = self._dragged, None
        self._cancel_autoscroll()
        if self.on_drag_state:
            self.on_drag_state(dragged[1], False)
        if self.order() != self._start_order:
            self.on_drop(self.order())

    # --- layout ----------------------------------------------------------

    def _follow_pointer(self) -> None:
        dragged = self._dragged
        if dragged is None or not dragged[1].winfo_exists():
            return
        others = [item for item in self.rows if item is not dragged]
        # The target slot is the number of other rows whose middle lies above
        # the pointer. Rows move by the dragged row's height when it passes
        # them, which keeps their middles on the far side — no flicker.
        target = sum(
            1
            for _key, row in others
            if row.winfo_rooty() + row.winfo_height() / 2 < self._pointer_y
        )
        if self.rows.index(dragged) == target:
            return
        others.insert(target, dragged)
        self.rows = others
        for index, (_key, row) in enumerate(self.rows):
            row.grid_configure(row=index)
        dragged[1].update_idletasks()

    def _autoscroll(self) -> None:
        self._scroll_job = None
        if self._dragged is None or self.canvas is None:
            return
        top = self.canvas.winfo_rooty()
        bottom = top + self.canvas.winfo_height()
        step = 0
        if self._pointer_y < top + EDGE_ZONE:
            step = -1
        elif self._pointer_y > bottom - EDGE_ZONE:
            step = 1
        if step:
            first, last = self.canvas.yview()
            if (step < 0 and first > 0.0) or (step > 0 and last < 1.0):
                self.canvas.yview_scroll(step * 2, "units")
                self._follow_pointer()
        self._scroll_job = self.canvas.after(AUTOSCROLL_MS, self._autoscroll)

    def _cancel_autoscroll(self) -> None:
        if self._scroll_job and self.canvas is not None:
            try:
                self.canvas.after_cancel(self._scroll_job)
            except tk.TclError:
                pass
        self._scroll_job = None
