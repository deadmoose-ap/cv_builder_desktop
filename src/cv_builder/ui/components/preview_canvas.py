"""Canvas that draws the paginated CV exactly as it will be exported."""
from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from typing import Any

from cv_builder.exporters import page_style
from cv_builder.exporters.preview_layout import build_pages
from cv_builder.ui.components.scrollable import touchpad_scroll_dy
from cv_builder.ui.theme import COLORS


PAGE_GAP = 22.0
MIN_SCALE = 0.5
MAX_SCALE = 1.0
PAGE_MARGIN = 16.0
PREVIEW_FONT = "Arial"
# Tk cannot load a font file, so the preview draws CJK with whatever the system
# installs. Glyph shapes may differ slightly from the embedded Noto in the
# export; line breaks and page count do not, because `preview_layout` measures
# with the exported font itself.
CJK_PREVIEW_FONTS = {
    "ja": ("Hiragino Sans", "Yu Gothic UI", "Arial Unicode MS"),
    "ko": ("Apple SD Gothic Neo", "Malgun Gothic", "Arial Unicode MS"),
    "zh-Hans": ("PingFang SC", "Microsoft YaHei UI", "Arial Unicode MS"),
    "zh-Hant": ("PingFang TC", "Microsoft JhengHei UI", "Arial Unicode MS"),
}


class PreviewCanvas(tk.Canvas):
    """Draws every page at a scale that fits the available area."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            background=COLORS["background"],
            highlightthickness=0,
            borderwidth=0,
            **kwargs,
        )
        self.data: dict[str, Any] | None = None
        self._redraw_job: str | None = None
        # Pixel-sized scroll units; the default (0) makes one unit a tenth
        # of the window, far too coarse for per-event trackpad deltas.
        self.configure(yscrollincrement=8)
        self.bind("<Configure>", self._schedule_redraw, add="+")
        self.bind("<MouseWheel>", self._on_wheel, add="+")
        self.bind("<Button-4>", self._on_wheel, add="+")
        self.bind("<Button-5>", self._on_wheel, add="+")
        try:
            self.bind("<TouchpadScroll>", self._on_touchpad, add="+")
        except tk.TclError:
            pass  # Tk < 9 has no <TouchpadScroll>; trackpads send <MouseWheel>


    def render(self, data: dict[str, Any]) -> None:
        self.data = data
        self._draw()

    def _schedule_redraw(self, _event=None) -> None:
        if self._redraw_job:
            self.after_cancel(self._redraw_job)
        self._redraw_job = self.after(60, self._draw)

    def _on_wheel(self, event) -> None:
        if event.num == 4:
            steps = -3
        elif event.num == 5:
            steps = 3
        else:
            steps = -event.delta
            if abs(steps) >= 120:
                steps = int(steps / 120) * 3
        self.yview_scroll(int(steps), "units")

    def _on_touchpad(self, event) -> None:
        dy = touchpad_scroll_dy(event)
        if dy:
            self.yview_scroll(-dy, "units")

    def _font_family(self) -> str:
        """Pick the first installed family that can draw this CV's script."""
        locale = (self.data or {}).get("locale")
        candidates = CJK_PREVIEW_FONTS.get(locale or "")
        if not candidates:
            return PREVIEW_FONT
        installed = set(tkfont.families(self))
        return next((name for name in candidates if name in installed), PREVIEW_FONT)

    def _page_scale(self) -> float:
        """Fit the page width, never magnifying past 1:1; height scrolls."""
        width = max(self.winfo_width() - 48, 120)
        return min(MAX_SCALE, max(MIN_SCALE, width / page_style.PAGE_WIDTH))

    def _draw(self) -> None:
        self._redraw_job = None
        self.delete("all")
        if not self.data:
            return
        if self.winfo_width() <= 50:
            # Laid out but not sized yet — draw once the geometry is real.
            self._schedule_redraw()
            return
        scale = self._page_scale()
        page_width = page_style.PAGE_WIDTH * scale
        page_height = page_style.PAGE_HEIGHT * scale
        gap = PAGE_GAP * scale
        left = max((self.winfo_width() - page_width) / 2, 12)

        pages = build_pages(self.data)
        family = self._font_family()
        for index, page in enumerate(pages):
            top = PAGE_MARGIN + index * (page_height + gap)
            self.create_rectangle(
                left,
                top,
                left + page_width,
                top + page_height,
                fill="#FFFFFF",
                outline=COLORS["border"],
            )
            self.create_rectangle(
                left,
                top,
                left + page_style.SIDEBAR_WIDTH * scale,
                top + page_height,
                fill=page.sidebar_color,
                outline=page.sidebar_color,
            )
            for line in page.lines:
                self.create_text(
                    left + line.x * scale,
                    top + line.y * scale,
                    text=line.text,
                    anchor=line.anchor,
                    fill=line.color,
                    font=(family, -max(int(round(line.size * scale)), 5)),
                )
        total = 2 * PAGE_MARGIN + len(pages) * (page_height + gap)
        self.configure(scrollregion=(0, 0, self.winfo_width(), total))
