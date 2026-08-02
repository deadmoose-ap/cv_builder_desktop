"""Placeholder copy for the form fields.

Placeholders are UI state only ([PHD]): they are never saved, exported or
counted towards completion. They follow the *interface* language, because they
are hints addressed to the person filling the form — not content of the CV,
which carries its own locale (`domain.locales`).

The strings themselves live with the rest of the interface copy under the
`placeholder.` prefix in `ui/strings/`; this module is the lookup those forms
go through.
"""
from __future__ import annotations

from cv_builder.ui.i18n import placeholders


def placeholders_for(locale: str | None = None) -> dict[str, str]:
    """Field name -> hint text for an interface locale."""
    return placeholders(locale)
