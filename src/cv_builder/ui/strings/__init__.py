"""Interface translations, one module per locale. See `ui.i18n`.

Every locale is imported **statically** here on purpose. PyInstaller resolves
imports by static analysis, so a dynamic `import_module(f"...strings.{code}")`
is invisible to it and the whole package is dropped from the bundle — the app
then starts fine from source and crashes only in the built `.app`. Listing the
modules here keeps them in the frozen archive and gives one place to register
a new language.
"""
from __future__ import annotations

from cv_builder.ui.strings import de, en, es, fr, ja, ko, ru, zh_hans, zh_hant


STRINGS_BY_LOCALE: dict[str, dict[str, str]] = {
    "en": en.STRINGS,
    "ru": ru.STRINGS,
    "de": de.STRINGS,
    "es": es.STRINGS,
    "fr": fr.STRINGS,
    "ja": ja.STRINGS,
    "ko": ko.STRINGS,
    "zh-Hant": zh_hant.STRINGS,
    "zh-Hans": zh_hans.STRINGS,
}
