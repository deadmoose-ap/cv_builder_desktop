"""Interface strings, kept out of the widgets that display them.

`DESKTOP_APP_ARCHITECTURE.md` §7 asks for exactly this: "UI strings should be
extracted from widgets before a second language is added."

Translations are Python modules rather than JSON data files on purpose: there
is nothing to declare in `datas` and nothing to read from disk at runtime
([LFO]). They are registered statically in `ui/strings/__init__.py` — see the
note there on why a dynamic import would not survive packaging.

This layer covers the *interface* only. The static headings printed inside an
exported CV are a property of the document and live in `domain.cv_labels`.
"""
from __future__ import annotations

from typing import Any

from cv_builder.domain.locales import LOCALE_CODES
from cv_builder.infrastructure.settings import DEFAULT_UI_LOCALE
from cv_builder.ui.strings import STRINGS_BY_LOCALE


def _load(code: str) -> dict[str, str]:
    return STRINGS_BY_LOCALE[code]


def is_supported(code: str | None) -> bool:
    return code in LOCALE_CODES


class Translator:
    """Look up an interface string by key, falling back to English."""

    def __init__(self, code: str | None = None):
        self.code = code if is_supported(code) else DEFAULT_UI_LOCALE
        self._fallback = _load(DEFAULT_UI_LOCALE)
        self._strings = (
            self._fallback if self.code == DEFAULT_UI_LOCALE else _load(self.code)
        )

    def __call__(self, key: str, **kwargs: Any) -> str:
        # A missing key must never crash a window mid-build: show the key so the
        # gap is obvious in a screenshot instead of silently blank.
        value = self._strings.get(key) or self._fallback.get(key) or key
        return value.format(**kwargs) if kwargs else value

    # Reads better than `t("…")` at call sites that already hold a translator.
    def get(self, key: str, **kwargs: Any) -> str:
        return self(key, **kwargs)


def placeholders(code: str | None = None) -> dict[str, str]:
    """Field hint text for a locale ([PHD]: UI state, never document data)."""
    translator = Translator(code)
    return {
        key.removeprefix("placeholder."): translator(key)
        for key in translator._fallback
        if key.startswith("placeholder.")
    }
