"""Page layouts a CV can be exported in.

A layout is a document property, like the theme and the locale: it is stored in
the CV JSON and travels with an exported file.

- ``sidebar`` — the coloured plate on the left with contacts and short lists.
  Meant for a CV sent directly to a person.
- ``single`` — one column, contacts in the body, nothing drawn outside the text
  flow. Meant for applicant tracking systems, whose parsers read a sidebar
  before the name or mix it into the main column.

Labels are interface copy and live in `ui/strings`, not here.
"""
from __future__ import annotations


LAYOUTS: tuple[dict[str, str], ...] = (
    {"key": "sidebar"},
    {"key": "single"},
)
DEFAULT_LAYOUT = LAYOUTS[0]["key"]
SINGLE = "single"


def get_layout(key: str | None) -> dict[str, str]:
    """Return a known layout, falling back to the default one."""
    for layout in LAYOUTS:
        if layout["key"] == key:
            return layout
    return LAYOUTS[0]


def is_single(key: str | None) -> bool:
    return get_layout(key)["key"] == SINGLE
