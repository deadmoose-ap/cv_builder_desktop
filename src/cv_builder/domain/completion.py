"""How complete a CV is — a simple, explainable percentage."""
from __future__ import annotations

from typing import Any


def calculate_completion(data: dict[str, Any]) -> int:
    """Return the share of filled top-level fields, rounded to a percent."""
    profile = data.get("profile", {})
    education = data.get("education", {})
    checks = (
        bool(profile.get("name")),
        bool(profile.get("headline")),
        bool(profile.get("location")),
        bool(profile.get("email")),
        bool(profile.get("linkedin")),
        bool(profile.get("skills")),
        bool(profile.get("summary")),
        bool(data.get("experience")),
        bool(education.get("institution")),
        bool(education.get("qualification")),
    )
    return round(sum(bool(value) for value in checks) / len(checks) * 100)
