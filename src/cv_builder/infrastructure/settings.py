"""Application-level preferences, stored next to the CV library.

The first setting that is not a property of any single document: the interface
language. Kept deliberately separate from the per-CV `locale` key in the
document JSON — the two are switched independently.

Same [ATP] contract as the library: UTF-8 JSON written to a temporary file and
atomically moved into place. Reading is forgiving by design: a missing or
corrupt file yields defaults instead of blocking the app from starting.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

from cv_builder.domain.locales import LOCALE_CODES
from cv_builder.infrastructure.library import application_data_dir


DEFAULT_UI_LOCALE = "en"


@dataclass(frozen=True)
class AppSettings:
    """Preferences that belong to the installation, not to a document."""

    ui_locale: str = DEFAULT_UI_LOCALE


class SettingsStore:
    """Read and write `settings.json` in the application data directory."""

    def __init__(self, root: str | Path | None = None):
        self.root = Path(root) if root else application_data_dir()
        self.path = self.root / "settings.json"

    def load(self) -> AppSettings:
        """Return stored preferences; anything unreadable falls back to defaults."""
        try:
            with self.path.open("r", encoding="utf-8") as stream:
                stored = json.load(stream)
        except (OSError, json.JSONDecodeError):
            return AppSettings()
        if not isinstance(stored, dict):
            return AppSettings()
        return self._from_dict(stored)

    def _from_dict(self, stored: dict[str, Any]) -> AppSettings:
        # The interface offers the same nine languages a CV can be written in,
        # so the domain list is the single source of truth for valid codes.
        locale = stored.get("ui_locale")
        if not isinstance(locale, str) or locale not in LOCALE_CODES:
            locale = DEFAULT_UI_LOCALE
        return AppSettings(ui_locale=locale)

    def save(self, settings: AppSettings) -> AppSettings:
        self.root.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".json.tmp")
        with temporary.open("w", encoding="utf-8") as stream:
            json.dump(asdict(settings), stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        temporary.replace(self.path)
        return settings

    def set_ui_locale(self, code: str) -> AppSettings:
        return self.save(replace(self.load(), ui_locale=code))
