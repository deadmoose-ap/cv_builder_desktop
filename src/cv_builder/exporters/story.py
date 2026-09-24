"""Layout-independent description of a rendered CV.

The story is a flat list of paragraphs, gaps and keep-together groups. The PDF
exporter turns it into ReportLab flowables; the preview turns it into canvas
lines. Only one module decides what the document contains.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Union

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
    """Contact and optional sidebar lists, drawn on the first page only."""
    profile = data.get("profile", {})
    text = labels(data.get("locale"))
    story: list[Item] = []

    def add_block(title: str, values: Iterable[Any], *, bullet: bool = False) -> None:
        cleaned = _clean(values)
        if not cleaned:
            return
        if story:
            story.append(Gap(9))
        story.append(Para(title, "side_head"))
        style = "side_bullet" if bullet else "side_body"
        story.extend(
            Para(value if not bullet else f"{BULLET}{value}", style)
            for value in cleaned
        )

    add_block(
        text["contact"],
        (profile.get("email"), profile.get("linkedin"), profile.get("telegram")),
    )
    add_block(text["portfolio"], profile.get("portfolio", []), bullet=True)
    add_block(text["languages"], profile.get("languages", []), bullet=True)
    add_block(text["core_skills"], profile.get("skills", []), bullet=True)
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
        if body:
            body.append(Gap(5))
        body.append(
            Group(
                (
                    Para(text[label_key], "subhead"),
                    Para(f"{BULLET}{values[0]}", "bullet"),
                )
            )
        )
        body += [Para(f"{BULLET}{value}", "bullet") for value in values[1:]]
    return body


def _experience_story(
    data: dict[str, Any],
    position_header: Callable[[dict[str, Any], str | None], list[Para]],
) -> list[Item]:
    """Every company and its positions; ``position_header`` shapes each header."""
    text = labels(data.get("locale"))
    locale = data.get("locale")
    experience_story: list[Item] = []
    for entry in data.get("experience", []):
        positions = entry.get("positions") or []
        company = company_line(entry, locale)
        entry_story: list[Item] = []
        if positions:
            # The company name is kept with the first position's header so a
            # page break can never orphan it; later positions carry their own
            # header.
            for index, position in enumerate(positions):
                header: list[Para] = []
                if index == 0 and company.strip():
                    header.append(Para(company, "company"))
                header += position_header(position, locale)
                if header:
                    entry_story.append(Group(tuple(header)))
                entry_story += _position_body(position, text)
                if index < len(positions) - 1 and entry_story:
                    entry_story.append(Gap(6))
        elif company.strip():
            entry_story.append(Group((Para(company, "company"),)))
        if entry_story:
            experience_story += entry_story
            experience_story.append(Gap(12))
    return experience_story


def main_story(data: dict[str, Any]) -> list[Item]:
    """Profile, summary, experience and education in reading order."""
    profile = data.get("profile", {})
    text = labels(data.get("locale"))
    story: list[Item] = []
    for key, style_name in (
        ("name", "name"),
        ("headline", "headline"),
        ("location", "location"),
    ):
        value = str(profile.get(key, "") or "")
        if value.strip():
            story.append(Para(value, style_name))

    summary = _clean(profile.get("summary", []))
    if summary:
        story.append(Para(text["summary"], "section"))
        story += [Para(value) for value in summary]

    experience_story = _experience_story(data, _position_header)
    if experience_story:
        story.append(Para(text["experience"], "section"))
        story += experience_story

    education = data.get("education", {})
    education_items: list[Para] = []
    for key, style_name in (("institution", "company"), ("qualification", "dates")):
        value = str(education.get(key, "") or "")
        if value.strip():
            education_items.append(Para(value, style_name))
    if education_items:
        story.append(Para(text["education"], "section"))
        story += education_items
    return story


# A non-breaking space inside each item and before the pipe: a line may only
# break after a separator, so a multi-word skill never splits across lines.
NBSP = " "
INLINE_SEPARATOR = f"{NBSP}| "


def inline_list(values: Iterable[Any]) -> str:
    """Skills or languages as one paragraph, broken only at the separators."""
    return INLINE_SEPARATOR.join(value.replace(" ", NBSP) for value in _clean(values))


def _single_position_header(position: dict[str, Any], locale: str | None) -> list[Para]:
    """Role, dates and duration on one line, then the location.

    ATS parsers pair a job title with the dates printed next to it; a separate
    dates line is easily attributed to the wrong role.
    """
    # The period and the duration each stay whole ("1 year 1 month" never ends
    # one line and starts the next); the line breaks only at a separator.
    dates_parts = position_dates_line(position, locale).split(META_SEPARATOR)
    role_line = META_SEPARATOR.join(
        _clean((position.get("role", ""), *(part.replace(" ", NBSP) for part in dates_parts)))
    )
    lines = ((role_line, "role"), (str(position.get("place", "")), "place"))
    return [Para(text, style) for text, style in lines if text.strip()]


def _section(heading: str, items: list[Item]) -> list[Item]:
    """A heading glued to its first block, so a page never ends on a heading."""
    if not items:
        return []
    first, rest = items[0], items[1:]
    if isinstance(first, Group):
        return [Group((Para(heading, "section"), *first.items)), *rest]
    if isinstance(first, Para):
        return [Group((Para(heading, "section"), first)), *rest]
    return [Para(heading, "section"), *items]


def single_column_story(data: dict[str, Any]) -> list[Item]:
    """The whole CV as one column in reading order, for ATS parsers.

    Everything the sidebar layout prints on the plate — contacts, portfolio,
    skills and languages — moves into the text flow, so the PDF text layer
    starts with the name, headline and contacts and nothing lies outside it.
    """
    profile = data.get("profile", {})
    text = labels(data.get("locale"))
    story: list[Item] = []
    for key, style_name in (("name", "name"), ("headline", "headline")):
        value = str(profile.get(key, "") or "")
        if value.strip():
            story.append(Para(value, style_name))
    contact = META_SEPARATOR.join(
        _clean(
            (
                profile.get("location"),
                profile.get("email"),
                profile.get("linkedin"),
                profile.get("telegram"),
            )
        )
    )
    if contact:
        story.append(Para(contact, "contact"))
    story += [Para(value, "portfolio") for value in _clean(profile.get("portfolio", []))]
    if story:
        story.append(Gap(10))

    story += _section(
        text["summary"], [Para(value) for value in _clean(profile.get("summary", []))]
    )
    skills = inline_list(profile.get("skills", []))
    story += _section(text["core_skills"], [Para(skills, "inline")] if skills else [])
    story += _section(
        text["experience"], _experience_story(data, _single_position_header)
    )

    education = data.get("education", {})
    education_items = [
        Para(str(education[key]), style_name)
        for key, style_name in (("institution", "company"), ("qualification", "dates"))
        if str(education.get(key, "") or "").strip()
    ]
    if education_items:
        # One short block: kept whole, not just glued to the heading.
        story += _section(text["education"], [Group(tuple(education_items))])
    languages = inline_list(profile.get("languages", []))
    story += _section(text["languages"], [Para(languages, "inline")] if languages else [])
    return story
