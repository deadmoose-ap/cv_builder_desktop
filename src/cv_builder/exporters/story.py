"""Layout-independent description of a rendered CV.

The story is a flat list of paragraphs, gaps and keep-together groups. The PDF
exporter turns it into ReportLab flowables; the preview turns it into canvas
lines. Only one module decides what the document contains.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Union

from cv_builder.domain import dates
from cv_builder.domain.cv_labels import labels


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
META_SEPARATOR = "  ·  "


def _clean(values: Iterable[Any]) -> list[str]:
    return [str(value) for value in values if str(value).strip()]


def sidebar_story(data: dict[str, Any]) -> list[Item]:
    """Contact, skills and languages, drawn on the first page only."""
    profile = data.get("profile", {})
    text = labels(data.get("locale"))
    story: list[Item] = [
        Para(text["contact"], "side_head"),
        Para(str(profile.get("email", "")), "side_body"),
        Para(str(profile.get("linkedin", "")), "side_body"),
        Gap(12),
        Para(text["core_skills"], "side_head"),
        Para("\n".join(_clean(profile.get("skills", []))), "side_body"),
    ]
    languages = _clean(profile.get("languages", []))
    if languages:
        story += [
            Gap(12),
            Para(text["languages"], "side_head"),
            Para("\n".join(languages), "side_body"),
        ]
    return story


def position_dates_line(position: dict[str, Any], locale: str | None) -> str:
    """"October 2025 – Present  ·  10 months", or the legacy text as written."""
    text = labels(locale)
    span = dates.format_range(
        position.get("start"),
        position.get("end"),
        bool(position.get("current")),
        locale,
        text["present"],
    )
    if not span:
        return META_SEPARATOR.join(
            _clean([position.get("dates_legacy"), position.get("duration_legacy")])
        )
    bounds = dates.interval(
        position.get("start"), position.get("end"), bool(position.get("current"))
    )
    length = dates.format_duration(
        bounds[1] - bounds[0] + 1 if bounds else 0, locale
    )
    return META_SEPARATOR.join(part for part in (span, length) if part)


def company_months(positions: list[dict[str, Any]]) -> int:
    """Months worked at one company, overlapping positions counted once."""
    bounds = [
        dates.interval(item.get("start"), item.get("end"), bool(item.get("current")))
        for item in positions
    ]
    return dates.union_months([value for value in bounds if value])


def company_line(entry: dict[str, Any], locale: str | None) -> str:
    """The company name, with the combined tenure when it holds several roles.

    A single position already prints its own duration next to its dates, so the
    total would only repeat it.
    """
    company = str(entry.get("company", ""))
    positions = entry.get("positions") or []
    if len(positions) < 2:
        return company
    total = dates.format_duration(company_months(positions), locale)
    return f"{company} ({total})" if total and company else company


def _position_header(position: dict[str, Any], locale: str | None) -> list[Para]:
    """Role, then dates and duration, then location — the mockup's ladder."""
    lines = (
        (str(position.get("role", "")), "role"),
        (position_dates_line(position, locale), "dates"),
        (str(position.get("place", "")), "place"),
    )
    return [Para(text, style) for text, style in lines if text.strip()]


def _position_body(position: dict[str, Any], text: dict[str, str]) -> list[Item]:
    body: list[Item] = []
    if position.get("intro"):
        body += [Gap(5), Para(str(position["intro"]))]
    for label_key, key in (("key_responsibilities", "work"), ("results", "results")):
        values = _clean(position.get(key, []))
        if not values:
            continue
        label = f"{text[label_key]}{text['list_suffix']}"
        body.append(Para(f"{label}\n{BULLET}{values[0]}"))
        body += [Para(f"{BULLET}{value}", "bullet") for value in values[1:]]
    return body


def main_story(data: dict[str, Any]) -> list[Item]:
    """Profile, summary, experience and education in reading order."""
    profile = data.get("profile", {})
    text = labels(data.get("locale"))
    story: list[Item] = [
        Para(str(profile.get("name", "")), "name"),
        Para(str(profile.get("headline", "")), "headline"),
        Para(str(profile.get("location", "")), "location"),
        Para(text["summary"], "section"),
    ]
    story += [Para(value) for value in _clean(profile.get("summary", []))]
    story.append(Para(text["experience"], "section"))

    locale = data.get("locale")
    for entry in data.get("experience", []):
        positions = entry.get("positions") or []
        # The company name is kept with the first position's header so a page
        # break can never orphan it; later positions carry their own header.
        header: list[Para] = [Para(company_line(entry, locale), "company")]
        for index, position in enumerate(positions or [{}]):
            header += _position_header(position, locale)
            story.append(Group(tuple(header)))
            story += _position_body(position, text)
            header = []
            if index < len(positions) - 1:
                story.append(Gap(6))
        story.append(Gap(12))

    education = data.get("education", {})
    story += [
        Para(text["education"], "section"),
        Para(str(education.get("institution", "")), "company"),
        Para(str(education.get("qualification", "")), "dates"),
    ]
    return story
