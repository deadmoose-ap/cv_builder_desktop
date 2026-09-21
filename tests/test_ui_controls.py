from types import SimpleNamespace
import os

import customtkinter as ctk
import pytest

from cv_builder.ui.components.fields import (
    dispatch_mac_edit_shortcut,
    mac_edit_action,
)
from cv_builder.ui.components.scrollable import AutoHideScrollableFrame


def test_mac_edit_action_uses_command_and_physical_keycode():
    event = SimpleNamespace(state=0x8, keycode=8)
    assert mac_edit_action(event, windowing_system="aqua") == "Copy"
    assert mac_edit_action(
        SimpleNamespace(state=0x8, keycode=9), windowing_system="aqua"
    ) == "Paste"
    assert mac_edit_action(
        SimpleNamespace(state=0x8, keycode=7), windowing_system="aqua"
    ) == "Cut"
    assert mac_edit_action(
        SimpleNamespace(state=0x8, keycode=0), windowing_system="aqua"
    ) == "SelectAll"
    assert mac_edit_action(event, windowing_system="x11") is None
    assert mac_edit_action(event, windowing_system="win32") is None
    assert mac_edit_action(SimpleNamespace(state=0, keycode=8), windowing_system="aqua") is None


def test_mac_edit_shortcut_dispatches_one_virtual_event():
    generated = []

    class Widget:
        class Tk:
            @staticmethod
            def call(*_args):
                return "aqua"

        tk = Tk()

        def event_generate(self, sequence):
            generated.append(sequence)

    result = dispatch_mac_edit_shortcut(
        Widget(), SimpleNamespace(state=0x8, keycode=8)
    )
    assert result == "break"
    assert generated == ["<<Copy>>"]


def test_mac_edit_shortcut_does_not_dispatch_on_non_aqua():
    generated = []

    class Widget:
        class Tk:
            @staticmethod
            def call(*_args):
                return "x11"

        tk = Tk()

        def event_generate(self, sequence):
            generated.append(sequence)

    result = dispatch_mac_edit_shortcut(
        Widget(), SimpleNamespace(state=0x8, keycode=8)
    )
    assert result is None
    assert generated == []


def test_scroll_target_boundary_arbitration():
    class Target:
        def __init__(self, view):
            self.view = view

        def yview(self):
            return self.view

    assert AutoHideScrollableFrame._target_can_scroll(Target((0.2, 0.8)), -1)
    assert not AutoHideScrollableFrame._target_can_scroll(Target((0.0, 0.8)), -1)
    assert not AutoHideScrollableFrame._target_can_scroll(Target((0.2, 1.0)), 1)
    assert not AutoHideScrollableFrame._target_can_scroll(Target((0.0, 1.0)), 1)


def test_live_text_scroll_arbitrates_before_parent_canvas():
    """The real CTkTextbox wrapper must bind only its inner tk.Text handler."""
    if os.environ.get("CV_BUILDER_LIVE_TK_TEST") != "1":
        pytest.skip("set CV_BUILDER_LIVE_TK_TEST=1 for a real Tk window")
    try:
        root = ctk.CTk()
    except Exception as exc:  # no display in CI/headless environments
        pytest.skip(f"Tk window unavailable: {exc}")
    try:
        root.geometry("420x220")
        frame = AutoHideScrollableFrame(root, width=300, height=120)
        frame.pack(fill="both", expand=True)
        textbox = ctk.CTkTextbox(frame, width=280, height=80)
        textbox.pack(fill="x")
        textbox._textbox.insert("1.0", "\n".join(f"line {i}" for i in range(100)))
        ctk.CTkLabel(frame, text="outer tail").pack(pady=180)
        root.update_idletasks()
        frame._bind_mousewheel(frame)
        text = textbox._textbox
        assert not getattr(textbox, "_cv_wheel_bound", False)
        assert getattr(text, "_cv_inner_wheel_bound", False)
        assert frame._parent_canvas.yview()[1] < 1.0
        assert int(frame._parent_canvas.cget("yscrollincrement")) == 8

        text.yview_moveto(0.4)
        root.update_idletasks()
        inner_before = text.yview()
        parent_before = frame._parent_canvas.yview()
        frame._on_text_mousewheel(SimpleNamespace(widget=text, num=0, delta=120))
        assert text.yview() != inner_before
        assert frame._parent_canvas.yview() == parent_before

        text.yview_moveto(1.0)
        parent_before = frame._parent_canvas.yview()
        frame._on_text_mousewheel(SimpleNamespace(widget=text, num=0, delta=-120))
        assert frame._parent_canvas.yview() != parent_before

        frame._parent_canvas.yview_moveto(0.4)
        parent_before = frame._parent_canvas.yview()
        frame._on_touchpad(SimpleNamespace(delta=16))
        assert frame._parent_canvas.yview() != parent_before

        assert text.bind("<MouseWheel>")
        try:
            touchpad_binding = text.bind("<TouchpadScroll>")
        except Exception:
            touchpad_binding = ""
        if touchpad_binding:
            assert getattr(text, "_cv_inner_wheel_bound", False)
    finally:
        root.destroy()
