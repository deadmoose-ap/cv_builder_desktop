"""Languages a CV can be written in.

A locale is a document property, like the sidebar theme: it is stored in the CV
JSON and travels with an exported file, so the same document renders with the
same section headings on any machine. The interface language is a separate,
independently switchable setting (`infrastructure.settings`).

Labels are written in their own script — a user picking Japanese should not
have to read the word "Japanese" in English first.
"""
from __future__ import annotations


LOCALES: tuple[dict[str, str], ...] = (
    {"code": "en", "label": "English"},
    {"code": "ru", "label": "Русский"},
    {"code": "de", "label": "Deutsch"},
    {"code": "es", "label": "Español"},
    {"code": "fr", "label": "Français"},
    {"code": "ja", "label": "日本語"},
    {"code": "ko", "label": "한국어"},
    {"code": "zh-Hant", "label": "繁體中文"},
    {"code": "zh-Hans", "label": "简体中文"},
)
DEFAULT_LOCALE = LOCALES[0]["code"]

LOCALE_CODES = tuple(locale["code"] for locale in LOCALES)

# Scripts written without spaces between words: they need a font with CJK
# glyphs and character-level line breaking, not whitespace-level.
CJK_LOCALES = frozenset({"ja", "ko", "zh-Hans", "zh-Hant"})


def get_locale(code: str | None) -> dict[str, str]:
    """Return a known locale, falling back to the default one."""
    for locale in LOCALES:
        if locale["code"] == code:
            return locale
    return LOCALES[0]


def locale_label(code: str | None) -> str:
    return get_locale(code)["label"]


def is_cjk(code: str | None) -> bool:
    return code in CJK_LOCALES
