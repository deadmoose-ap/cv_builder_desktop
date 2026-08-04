"""Data model and JSON persistence for CV Builder."""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from cv_builder.domain.dates import parse_legacy_range
from cv_builder.domain.locales import DEFAULT_LOCALE, get_locale
from cv_builder.domain.themes import DEFAULT_THEME, get_theme


# 1 -> one experience entry per role, dates as free text.
# 2 -> one entry per company holding a list of positions with real month dates.
SCHEMA_VERSION = 2

EXAMPLE_DATA: dict[str, Any] = {
    "schema_version": SCHEMA_VERSION,
    "profile": {
        "name": "YOUR NAME",
        "headline": "YOUR JOB TITLE | YOUR SPECIALIZATION | YOUR KEY VALUE",
        "location": "YOUR CITY, YOUR COUNTRY",
        "email": "your.email@example.com",
        "linkedin": "linkedin.com/in/your-profile",
        "skills": ["SKILL ONE", "SKILL TWO", "SKILL THREE"],
        "languages": ["English - C1", "Spanish - B2"],
        "summary": [
            "Write a short introduction about your professional background and main expertise.",
            "Describe the teams, projects, or products you have worked with.",
            "Highlight your most relevant results and areas of specialization.",
        ],
    },
    "experience": [
        {
            "company": "CURRENT OR MOST RECENT COMPANY",
            "positions": [
                {
                    "role": "YOUR CURRENT JOB TITLE",
                    "start": "2024-06",
                    "end": "",
                    "current": True,
                    "place": "CITY, COUNTRY",
                    "intro": "Add a one-sentence role or project description.",
                    "work": [
                        "Describe a key responsibility.",
                        "Describe another contribution.",
                    ],
                    "results": ["Describe a measurable result or business impact."],
                },
                {
                    "role": "THE JOB TITLE YOU HELD BEFORE IT, AT THE SAME COMPANY",
                    "start": "2022-09",
                    "end": "2024-05",
                    "current": False,
                    "place": "CITY, COUNTRY",
                    "intro": "Add a one-sentence role or project description.",
                    "work": ["Describe a key responsibility."],
                    "results": ["Describe a measurable result or business impact."],
                },
            ],
        }
    ],
    "education": {
        "institution": "UNIVERSITY OR SCHOOL NAME",
        "qualification": "DEGREE OR QUALIFICATION (YEAR - YEAR)",
    },
    "theme": DEFAULT_THEME,
    "locale": DEFAULT_LOCALE,
}

DEFAULT_DATA: dict[str, Any] = {
    "schema_version": SCHEMA_VERSION,
    "profile": {
        "name": "",
        "headline": "",
        "location": "",
        "email": "",
        "linkedin": "",
        "skills": [],
        "languages": [],
        "summary": [],
    },
    "experience": [],
    "education": {
        "institution": "",
        "qualification": "",
    },
    "theme": DEFAULT_THEME,
    "locale": DEFAULT_LOCALE,
}


def new_document() -> dict[str, Any]:
    """Return an independent, empty CV document."""
    return deepcopy(DEFAULT_DATA)


def empty_experience() -> dict[str, Any]:
    """Return a blank company entry with every key present."""
    return {"company": "", "positions": []}


def empty_position() -> dict[str, Any]:
    """Return a blank position with every key present.

    `dates_legacy` and `duration_legacy` only ever hold text carried over from
    a schema-1 document whose free-text dates could not be read; they are
    printed verbatim until the user picks real dates, and stay empty otherwise.
    """
    return {
        "role": "",
        "start": "",
        "end": "",
        "current": False,
        "place": "",
        "intro": "",
        "work": [],
        "results": [],
        "dates_legacy": "",
        "duration_legacy": "",
    }


def example_document() -> dict[str, Any]:
    """Return a readable example users can edit and import."""
    return deepcopy(EXAMPLE_DATA)


def _normalize_position(raw: dict[str, Any]) -> dict[str, Any]:
    position = empty_position()
    position.update({key: value for key, value in raw.items() if key in position})
    position["current"] = bool(position.get("current"))
    position["work"] = list(position.get("work") or [])
    position["results"] = list(position.get("results") or [])
    for key in ("role", "start", "end", "place", "intro", "dates_legacy", "duration_legacy"):
        position[key] = str(position.get(key) or "")
    if position["current"]:
        position["end"] = ""
    return position


def _migrate_entry(raw: dict[str, Any]) -> dict[str, Any]:
    """Turn a schema-1 entry (one role, free-text dates) into a company."""
    position = _normalize_position(raw)
    parsed = parse_legacy_range(raw.get("dates"))
    if parsed is not None:
        position["start"], position["end"], position["current"] = parsed
    else:
        # Unreadable dates are kept as written rather than guessed at, so no
        # document ever loses information by being opened in a newer build.
        position["dates_legacy"] = str(raw.get("dates") or "")
        position["duration_legacy"] = str(raw.get("duration") or "")
    described = any(
        position[key]
        for key in ("role", "start", "intro", "dates_legacy", "work", "results")
    )
    return {
        "company": str(raw.get("company") or ""),
        "positions": [position] if described else [],
    }


def _normalize_entry(raw: dict[str, Any]) -> dict[str, Any]:
    if "positions" not in raw:
        return _migrate_entry(raw)
    if not isinstance(raw["positions"], list):
        raise ValueError("The positions of an experience entry must be a list.")
    for position in raw["positions"]:
        if not isinstance(position, dict):
            raise ValueError("Every position must be an object.")
    return {
        "company": str(raw.get("company") or ""),
        "positions": [_normalize_position(item) for item in raw["positions"]],
    }


def normalize_document(data: dict[str, Any]) -> dict[str, Any]:
    """Validate, migrate and fill optional keys of a CV document."""
    if not isinstance(data, dict):
        raise ValueError("The CV document must be a JSON object.")
    for key in ("profile", "experience", "education"):
        if key not in data:
            raise ValueError(f"Missing required section: {key}")
    if not isinstance(data["profile"], dict):
        raise ValueError("The profile section must be an object.")
    if not isinstance(data["experience"], list):
        raise ValueError("The experience section must be a list.")
    if not isinstance(data["education"], dict):
        raise ValueError("The education section must be an object.")

    normalized = new_document()
    normalized["profile"].update(
        {
            key: value
            for key, value in data["profile"].items()
            if key in normalized["profile"]
        }
    )
    for key in ("skills", "languages", "summary"):
        normalized["profile"][key] = list(normalized["profile"].get(key) or [])
    normalized["experience"] = []
    for raw_entry in data["experience"]:
        if not isinstance(raw_entry, dict):
            raise ValueError("Every experience entry must be an object.")
        normalized["experience"].append(_normalize_entry(raw_entry))
    normalized["education"].update(
        {
            key: value
            for key, value in data["education"].items()
            if key in normalized["education"]
        }
    )
    # Optional keys: documents written before themes or locales existed fall
    # back silently. The experience section is the one part that really changed
    # shape, so it carries a version — `_normalize_entry` detects and upgrades
    # schema-1 entries on both load and import.
    normalized["theme"] = get_theme(data.get("theme"))["key"]
    normalized["locale"] = get_locale(data.get("locale"))["code"]
    normalized["schema_version"] = SCHEMA_VERSION
    return normalized


def load_document(path: str | Path) -> dict[str, Any]:
    """Load and minimally validate a CV JSON document."""
    with Path(path).open("r", encoding="utf-8") as stream:
        data = json.load(stream)
    return normalize_document(data)


def save_document(path: str | Path, data: dict[str, Any]) -> None:
    """Save a CV document as readable UTF-8 JSON."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(f"{destination.suffix}.tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(normalize_document(data), stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    temporary.replace(destination)
