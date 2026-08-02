"""Layout-independent description of a rendered CV.

The story is a flat list of paragraphs, gaps and keep-together groups. The PDF
exporter turns it into ReportLab flowables; the preview turns it into canvas
lines. Only one module decides what the document contains.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Union


@dataclass(frozen=True)
class Para:
    """A single paragraph. ``\\n`` inside the text is a hard line break."""

    text: str
    style: str = "body"


@dataclass(frozen=True)
class Gap:
    """Vertical whitespace between paragraphs."""

    height: float


@dataclass(frozen=True)
class Group:
    """Paragraphs that must never be split across a page boundary."""

    items: tuple[Para, ...] = field(default_factory=tuple)


Item = Union[Para, Gap, Group]

BULLET = "• "


def _clean(values: Iterable[Any]) -> list[str]:
    return [str(value) for value in values if str(value).strip()]


def sidebar_story(profile: dict[str, Any]) -> list[Item]:
    """Contact and skills block, drawn on the first page only."""
    skills = _clean(profile.get("skills", []))
    return [
        Para("CONTACT", "side_head"),
        Para(str(profile.get("email", "")), "side_body"),
        Para(str(profile.get("linkedin", "")), "side_body"),
        Gap(12),
        Para("CORE SKILLS", "side_head"),
        Para("\n".join(skills), "side_body"),
    ]


def main_story(data: dict[str, Any]) -> list[Item]:
    """Profile, summary, experience and education in reading order."""
    profile = data.get("profile", {})
    story: list[Item] = [
        Para(str(profile.get("name", "")), "name"),
        Para(str(profile.get("headline", "")), "headline"),
        Para(str(profile.get("location", "")), "location"),
        Para("SUMMARY", "section"),
    ]
    story += [Para(value) for value in _clean(profile.get("summary", []))]
    story.append(Para("EXPERIENCE", "section"))

    for item in data.get("experience", []):
        header = [Para(str(item.get("company", "")), "company")]
        if item.get("duration"):
            header.append(Para(str(item["duration"]), "duration"))
        header.append(Para(str(item.get("role", "")), "role"))
        header.append(Para(str(item.get("dates", "")), "dates"))
        if item.get("place"):
            header.append(Para(str(item["place"]), "dates"))
        story.append(Group(tuple(header)))
        if item.get("intro"):
            story += [Gap(5), Para(str(item["intro"]))]
        for label, key in (("KEY RESPONSIBILITIES", "work"), ("RESULTS", "results")):
            values = _clean(item.get(key, []))
            if not values:
                continue
            story.append(Para(f"{label}:\n{BULLET}{values[0]}"))
            story += [Para(f"{BULLET}{value}", "bullet") for value in values[1:]]
        story.append(Gap(12))

    education = data.get("education", {})
    story += [
        Para("EDUCATION", "section"),
        Para(str(education.get("institution", "")), "company"),
        Para(str(education.get("qualification", "")), "dates"),
    ]
    return story
