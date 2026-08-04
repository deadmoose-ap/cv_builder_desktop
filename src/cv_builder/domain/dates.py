"""Month/year dates, ranges and durations for the experience section.

Dates are stored as ``"YYYY-MM"`` strings: sortable, unambiguous, and readable
in the example JSON handed to an LLM. Day precision is deliberately absent — a
CV states the month a role started, not the morning.

Everything here is pure and offline ([LFO]). Formatting follows the *CV* locale
(`domain.locales`), because a rendered date is content of the document, not
interface copy; the month-name table is reused by the form dropdowns, which is
why it lives in the domain layer rather than in `ui/strings/`.
"""
from __future__ import annotations

import re
from datetime import date


# Month names per locale. CJK entries carry their own unit suffix so the date
# patterns below can treat every locale the same way.
MONTH_NAMES: dict[str, tuple[str, ...]] = {
    "en": (
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ),
    "ru": (
        "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
    ),
    "de": (
        "Januar", "Februar", "März", "April", "Mai", "Juni",
        "Juli", "August", "September", "Oktober", "November", "Dezember",
    ),
    "es": (
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    ),
    "fr": (
        "janvier", "février", "mars", "avril", "mai", "juin",
        "juillet", "août", "septembre", "octobre", "novembre", "décembre",
    ),
    "ja": tuple(f"{number}月" for number in range(1, 13)),
    "ko": tuple(f"{number}월" for number in range(1, 13)),
    "zh-Hant": tuple(f"{number}月" for number in range(1, 13)),
    "zh-Hans": tuple(f"{number}月" for number in range(1, 13)),
}

# How a month name and a year combine. CJK locales put the year first; the
# month name already contains its unit.
DATE_PATTERN: dict[str, str] = {
    "en": "{month} {year}",
    "ru": "{month} {year}",
    "de": "{month} {year}",
    "es": "{month} de {year}",
    "fr": "{month} {year}",
    "ja": "{year}年{month}",
    "ko": "{year}년 {month}",
    "zh-Hant": "{year}年{month}",
    "zh-Hans": "{year}年{month}",
}

RANGE_SEPARATOR: dict[str, str] = {
    "en": " – ", "ru": " – ", "de": " – ", "es": " – ", "fr": " – ",
    "ja": "〜", "ko": " ~ ", "zh-Hant": "〜", "zh-Hans": "〜",
}

# Plural forms of "year" and "month", indexed by `plural_index`.
YEAR_FORMS: dict[str, tuple[str, ...]] = {
    "en": ("year", "years"),
    "ru": ("год", "года", "лет"),
    "de": ("Jahr", "Jahre"),
    "es": ("año", "años"),
    "fr": ("an", "ans"),
    "ja": ("年",), "ko": ("년",), "zh-Hant": ("年",), "zh-Hans": ("年",),
}
MONTH_FORMS: dict[str, tuple[str, ...]] = {
    "en": ("month", "months"),
    "ru": ("месяц", "месяца", "месяцев"),
    "de": ("Monat", "Monate"),
    "es": ("mes", "meses"),
    "fr": ("mois", "mois"),
    "ja": ("ヶ月",), "ko": ("개월",), "zh-Hant": ("個月",), "zh-Hans": ("个月",),
}

# CJK writes "1年8ヶ月" with no space anywhere; Korean separates the two parts
# but not the number from its unit.
_NUMBER_SPACE = {"ja": "", "ko": "", "zh-Hant": "", "zh-Hans": ""}
_PART_SPACE = {"ja": "", "zh-Hant": "", "zh-Hans": ""}

_DEFAULT = "en"
_YM = re.compile(r"^(\d{4})-(\d{1,2})$")


def _fallback(table: dict[str, object], locale: str | None):
    return table.get(locale or "", table[_DEFAULT])


# --- parsing and formatting a single month -------------------------------


def parse_ym(value: str | None) -> tuple[int, int] | None:
    """Return ``(year, month)`` for a stored ``"YYYY-MM"`` value."""
    match = _YM.match(str(value or "").strip())
    if not match:
        return None
    year, month = int(match.group(1)), int(match.group(2))
    return (year, month) if 1 <= month <= 12 else None


def make_ym(year: int, month: int) -> str:
    return f"{year:04d}-{month:02d}"


def format_ym(value: str | None, locale: str | None = None) -> str:
    """Render a stored month as the CV's locale writes it."""
    parsed = parse_ym(value)
    if parsed is None:
        return ""
    year, month = parsed
    names = _fallback(MONTH_NAMES, locale)
    return _fallback(DATE_PATTERN, locale).format(month=names[month - 1], year=year)


# --- month arithmetic ----------------------------------------------------


def _ordinal(value: str | None) -> int | None:
    parsed = parse_ym(value)
    return None if parsed is None else parsed[0] * 12 + parsed[1] - 1


def _today_ordinal(today: date | None = None) -> int:
    moment = today or date.today()
    return moment.year * 12 + moment.month - 1


def months_between(start: str | None, end: str | None) -> int:
    """Inclusive month count: a role held for one calendar month counts as 1."""
    first, last = _ordinal(start), _ordinal(end)
    if first is None or last is None or last < first:
        return 0
    return last - first + 1


def interval(
    start: str | None,
    end: str | None,
    current: bool = False,
    today: date | None = None,
) -> tuple[int, int] | None:
    """Return the half-open month ordinals of a position, or ``None``."""
    first = _ordinal(start)
    if first is None:
        return None
    last = _today_ordinal(today) if current else _ordinal(end)
    if last is None or last < first:
        return None
    return (first, last)


def union_months(intervals: list[tuple[int, int]]) -> int:
    """Total months covered, counting overlapping positions only once."""
    total = 0
    reach: int | None = None
    for first, last in sorted(intervals):
        start = first if reach is None else max(first, reach + 1)
        if last >= start:
            total += last - start + 1
        reach = last if reach is None else max(reach, last)
    return total


# --- durations -----------------------------------------------------------


def plural_index(number: int, locale: str | None = None) -> int:
    """Index into the plural-form tuples above."""
    code = locale or _DEFAULT
    if code in ("ja", "ko", "zh-Hant", "zh-Hans"):
        return 0
    if code == "ru":
        if number % 10 == 1 and number % 100 != 11:
            return 0
        if 2 <= number % 10 <= 4 and not 12 <= number % 100 <= 14:
            return 1
        return 2
    if code == "fr":
        return 0 if number <= 1 else 1
    return 0 if number == 1 else 1


def _unit(number: int, forms: tuple[str, ...], locale: str | None) -> str:
    form = forms[min(plural_index(number, locale), len(forms) - 1)]
    return f"{number}{_NUMBER_SPACE.get(locale or '', ' ')}{form}"


def format_duration(months: int, locale: str | None = None) -> str:
    """Render a month count as "1 год 8 месяцев" / "10 months" / "1年8ヶ月"."""
    if months <= 0:
        return ""
    parts = []
    years, remainder = divmod(months, 12)
    if years:
        parts.append(_unit(years, _fallback(YEAR_FORMS, locale), locale))
    if remainder or not years:
        parts.append(_unit(remainder, _fallback(MONTH_FORMS, locale), locale))
    return _PART_SPACE.get(locale or "", " ").join(parts)


# --- ranges --------------------------------------------------------------


def format_range(
    start: str | None,
    end: str | None,
    current: bool,
    locale: str | None = None,
    present: str = "",
) -> str:
    """Render "October 2025 – Present"; `present` comes from `cv_labels`."""
    first = format_ym(start, locale)
    if not first:
        return ""
    last = present if current else format_ym(end, locale)
    if not last:
        return first
    return f"{first}{_fallback(RANGE_SEPARATOR, locale)}{last}"


# --- reading the free-text dates written before this schema ---------------

# Words every locale uses for an open-ended role, lower-cased.
_PRESENT_WORDS = (
    "present", "current", "now", "today",
    "настоящее время", "по настоящее время", "н.в.", "нв", "сейчас",
    "heute", "aktuell", "laufend",
    "actualidad", "presente", "actual",
    "aujourd'hui", "présent", "en cours",
    "現在", "현재", "至今", "迄今",
)
_RANGE_SPLIT = re.compile(r"\s*(?:—|–|~|〜|-{1,2}|\bto\b|\bпо\b|\bbis\b|\ba\b|\bà\b)\s*")
_NUMERIC_MONTH = re.compile(r"^(\d{1,2})[./](\d{4})$")
_NUMERIC_MONTH_FIRST_YEAR = re.compile(r"^(\d{4})[./-](\d{1,2})$")
_YEAR_ONLY = re.compile(r"^(\d{4})$")
_CJK_YM = re.compile(r"^(\d{4})\s*[年년]\s*(\d{1,2})\s*[月월]?$")


def _month_from_name(token: str) -> int | None:
    """Match a month name in any supported locale, full name or prefix."""
    cleaned = token.strip().strip(".,").lower()
    if not cleaned:
        return None
    for names in MONTH_NAMES.values():
        for index, name in enumerate(names, start=1):
            lowered = name.lower()
            if cleaned == lowered:
                return index
            # "Oct" / "окт" — only unambiguous prefixes of three or more.
            if len(cleaned) >= 3 and lowered.startswith(cleaned):
                return index
    return None


def _parse_digits_only(text: str) -> str | None:
    """Read "2025-10", "10.2025", "2025年10月" — forms with no month name."""
    for pattern, order in (
        (_CJK_YM, "ym"),
        (_NUMERIC_MONTH_FIRST_YEAR, "ym"),
        (_NUMERIC_MONTH, "my"),
    ):
        match = pattern.match(text.strip())
        if match:
            first, second = int(match.group(1)), int(match.group(2))
            year, month = (first, second) if order == "ym" else (second, first)
            return make_ym(year, month) if 1 <= month <= 12 else None
    return None


def parse_month_token(token: str) -> str | None:
    """Best-effort read of one side of a legacy free-text date range."""
    text = str(token or "").strip()
    if not text:
        return None
    digits = _parse_digits_only(text)
    if digits is not None:
        return digits
    # "October 2025", "Октябрь 2025", "2025 October", "octubre de 2025"
    words = [word for word in re.split(r"[\s,]+", text) if word]
    year = next((int(word) for word in words if _YEAR_ONLY.match(word)), None)
    if year is None:
        return None
    for word in words:
        month = _month_from_name(word)
        if month is not None:
            return make_ym(year, month)
    return None


def parse_legacy_range(text: str | None) -> tuple[str, str, bool] | None:
    """Read a pre-schema-2 ``dates`` string into ``(start, end, current)``.

    Returns ``None`` when the text cannot be read with confidence — the caller
    keeps the original string and prints it verbatim rather than guessing.
    """
    raw = str(text or "").strip()
    if not raw:
        return None
    # A bare numeric month must be read before splitting, or "2025-10" would be
    # torn apart by the hyphen that usually separates the ends of a range.
    single = _parse_digits_only(raw)
    if single is not None:
        return (single, "", False)
    parts = [part for part in _RANGE_SPLIT.split(raw) if part.strip()]
    if not parts:
        return None
    start = parse_month_token(parts[0])
    if start is None:
        return None
    if len(parts) == 1:
        return (start, "", False)
    tail = " ".join(parts[1:]).strip()
    if tail.lower().strip(".") in _PRESENT_WORDS or any(
        word in tail.lower() for word in _PRESENT_WORDS
    ):
        return (start, "", True)
    end = parse_month_token(tail)
    if end is None:
        return None
    return (start, end, False)
