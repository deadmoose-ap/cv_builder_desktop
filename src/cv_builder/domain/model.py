"""Data model and JSON persistence for CV Builder."""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from cv_builder.domain.locales import DEFAULT_LOCALE, get_locale
from cv_builder.domain.themes import DEFAULT_THEME, get_theme


EXAMPLE_DATA: dict[str, Any] = {
    "profile": {
        "name": "YOUR NAME",
        "headline": "YOUR JOB TITLE | YOUR SPECIALIZATION | YOUR KEY VALUE",
        "location": "YOUR CITY, YOUR COUNTRY",
        "email": "your.email@example.com",
        "linkedin": "linkedin.com/in/your-profile",
        "skills": ["SKILL ONE", "SKILL TWO", "SKILL THREE"],
        "summary": [
            "Write a short introduction about your professional background and main expertise.",
            "Describe the teams, projects, or products you have worked with.",
            "Highlight your most relevant results and areas of specialization.",
        ],
    },
    "experience": [
        {
            "company": "CURRENT OR MOST RECENT COMPANY",
            "duration": "X YEARS X MONTHS",
            "role": "YOUR JOB TITLE",
            "dates": "MONTH YEAR - PRESENT",
            "place": "CITY, COUNTRY",
            "intro": "Add a one-sentence role or project description.",
            "work": ["Describe a key responsibility.", "Describe another contribution."],
            "results": ["Describe a measurable result or business impact."],
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
    "profile": {
        "name": "",
        "headline": "",
        "location": "",
        "email": "",
        "linkedin": "",
        "skills": [],
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
    """Return a blank experience entry with every key present."""
    return {
        "company": "",
        "duration": "",
        "role": "",
        "dates": "",
        "place": "",
        "intro": "",
        "work": [],
        "results": [],
    }


def example_document() -> dict[str, Any]:
    """Return a readable example users can edit and import."""
    return deepcopy(EXAMPLE_DATA)


def normalize_document(data: dict[str, Any]) -> dict[str, Any]:
    """Validate and fill optional keys without changing the JSON schema."""
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
    normalized["profile"]["skills"] = list(
        normalized["profile"].get("skills") or []
    )
    normalized["profile"]["summary"] = list(
        normalized["profile"].get("summary") or []
    )
    normalized["experience"] = []
    for raw_entry in data["experience"]:
        if not isinstance(raw_entry, dict):
            raise ValueError("Every experience entry must be an object.")
        entry = empty_experience()
        entry.update({key: value for key, value in raw_entry.items() if key in entry})
        entry["work"] = list(entry.get("work") or [])
        entry["results"] = list(entry.get("results") or [])
        normalized["experience"].append(entry)
    normalized["education"].update(
        {
            key: value
            for key, value in data["education"].items()
            if key in normalized["education"]
        }
    )
    # Optional keys: documents written before themes or locales existed fall
    # back silently, so no migration or schema_version bump is required.
    normalized["theme"] = get_theme(data.get("theme"))["key"]
    normalized["locale"] = get_locale(data.get("locale"))["code"]
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
