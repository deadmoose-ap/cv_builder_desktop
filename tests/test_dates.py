"""Month dates, durations and the schema-1 experience migration."""
from datetime import date

import pytest

from cv_builder.domain import dates
from cv_builder.domain.locales import LOCALE_CODES
from cv_builder.domain.model import SCHEMA_VERSION, normalize_document
from cv_builder.exporters.story import company_line, main_story, position_dates_line


TODAY = date(2026, 8, 4)


def document(experience):
    return {
        "profile": {"name": "Alex"},
        "experience": experience,
        "education": {"institution": "", "qualification": ""},
        "locale": "ru",
    }


# --- formatting ----------------------------------------------------------


def test_every_locale_can_format_a_month_and_a_duration():
    for code in LOCALE_CODES:
        assert dates.format_ym("2025-10", code)
        assert dates.format_duration(20, code)
        assert code in dates.MONTH_NAMES
        assert len(dates.MONTH_NAMES[code]) == 12


@pytest.mark.parametrize(
    "locale, expected",
    [
        ("en", "October 2025"),
        ("ru", "Октябрь 2025"),
        ("es", "octubre de 2025"),
        ("ja", "2025年10月"),
        ("ko", "2025년 10월"),
        ("zh-Hans", "2025年10月"),
    ],
)
def test_month_order_follows_the_locale(locale, expected):
    assert dates.format_ym("2025-10", locale) == expected


@pytest.mark.parametrize(
    "months, expected",
    [(1, "1 месяц"), (3, "3 месяца"), (10, "10 месяцев"), (11, "11 месяцев"),
     (12, "1 год"), (24, "2 года"), (60, "5 лет"), (20, "1 год 8 месяцев")],
)
def test_russian_duration_uses_all_three_plural_forms(months, expected):
    assert dates.format_duration(months, "ru") == expected


def test_duration_is_empty_for_no_time_at_all():
    assert dates.format_duration(0, "en") == ""


def test_format_ym_ignores_values_it_cannot_read():
    for value in (None, "", "2025", "2025-13", "not a date"):
        assert dates.format_ym(value, "en") == ""


# --- arithmetic ----------------------------------------------------------


def test_months_between_counts_inclusively():
    assert dates.months_between("2025-10", "2025-10") == 1
    assert dates.months_between("2024-06", "2025-05") == 12
    assert dates.months_between("2025-10", "2025-09") == 0


def test_a_current_position_is_measured_against_today():
    bounds = dates.interval("2026-06", "", True, today=TODAY)
    assert bounds is not None
    assert bounds[1] - bounds[0] + 1 == 3


def test_overlapping_positions_are_counted_once():
    # Two roles sharing six months must not add up to two years.
    first = dates.interval("2024-01", "2024-12")
    second = dates.interval("2024-07", "2025-06")
    assert dates.union_months([first, second]) == 18
    assert dates.union_months([first, dates.interval("2025-01", "2025-06")]) == 18


def test_a_gap_between_positions_is_not_counted():
    assert dates.union_months(
        [dates.interval("2020-01", "2020-06"), dates.interval("2022-01", "2022-06")]
    ) == 12


# --- reading the free-text dates of schema-1 documents --------------------


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Октябрь 2025 - настоящее время", ("2025-10", "", True)),
        ("October 2025 – Present", ("2025-10", "", True)),
        ("Sep 2022 - May 2024", ("2022-09", "2024-05", False)),
        ("2022年9月〜2024年5月", ("2022-09", "2024-05", False)),
        ("10.2025", ("2025-10", "", False)),
        ("2025-10", ("2025-10", "", False)),
    ],
)
def test_legacy_ranges_are_read_when_they_can_be(text, expected):
    assert dates.parse_legacy_range(text) == expected


@pytest.mark.parametrize("text", ["", None, "somewhere in the past", "sometime - later"])
def test_unreadable_legacy_ranges_are_refused_rather_than_guessed(text):
    assert dates.parse_legacy_range(text) is None


def test_a_schema_1_entry_becomes_a_company_with_one_position():
    data = normalize_document(document([
        {
            "company": "Playrix",
            "duration": "10 месяцев",
            "role": "Project Manager",
            "dates": "Октябрь 2025 - настоящее время",
            "place": "Сербия",
            "intro": "Intro.",
            "work": ["Did the work"],
            "results": ["Shipped it"],
        }
    ]))
    assert data["schema_version"] == SCHEMA_VERSION
    entry = data["experience"][0]
    assert entry["company"] == "Playrix"
    position = entry["positions"][0]
    assert position["start"] == "2025-10"
    assert position["current"] is True
    assert position["place"] == "Сербия"
    assert position["work"] == ["Did the work"]
    assert not position["dates_legacy"]


def test_unreadable_legacy_dates_survive_verbatim():
    data = normalize_document(document([
        {"company": "Old", "role": "Dev", "dates": "some time ago", "duration": "2 года"}
    ]))
    position = data["experience"][0]["positions"][0]
    assert position["start"] == ""
    assert position["dates_legacy"] == "some time ago"
    assert position["duration_legacy"] == "2 года"
    # Nothing is lost: the original wording is what the PDF still prints.
    assert position_dates_line(position, "ru") == "some time ago  ·  2 года"


def test_a_schema_2_document_is_left_alone():
    original = document([
        {
            "company": "Playrix",
            "positions": [
                {"role": "PM", "start": "2025-10", "end": "", "current": True},
                {"role": "Dev", "start": "2022-09", "end": "2025-09", "current": False},
            ],
        }
    ])
    data = normalize_document(original)
    assert [item["role"] for item in data["experience"][0]["positions"]] == ["PM", "Dev"]
    assert data["experience"][0]["positions"][0]["end"] == ""


# --- what the rendered document says --------------------------------------


def test_a_company_shows_its_total_only_when_it_holds_several_roles():
    single = {"company": "Playrix", "positions": [
        {"role": "PM", "start": "2024-01", "end": "2024-12"}
    ]}
    assert company_line(single, "ru") == "Playrix"

    several = {"company": "Playrix", "positions": [
        {"role": "PM", "start": "2024-01", "end": "2024-12"},
        {"role": "Dev", "start": "2022-01", "end": "2023-12"},
    ]}
    assert company_line(several, "ru") == "Playrix (3 года)"


def test_the_experience_header_is_a_company_role_dates_place_ladder():
    data = normalize_document(document([
        {
            "company": "Playrix",
            "positions": [
                {
                    "role": "Project Manager",
                    "start": "2025-10",
                    "current": True,
                    "place": "Сербия",
                }
            ],
        }
    ]))
    group = next(
        item for item in main_story(data) if getattr(item, "items", None)
    )
    assert [para.style for para in group.items] == [
        "company", "role", "dates", "place"
    ]
    assert group.items[0].text == "Playrix"
    assert group.items[2].text.startswith("Октябрь 2025 – настоящее время  ·  ")


def test_the_company_name_is_bold_and_larger_than_the_role():
    from cv_builder.exporters import page_style

    company = page_style.style("company")
    assert company["bold"] is True
    assert company["size"] > page_style.style("role")["size"]
    assert page_style.style("role")["size"] > page_style.style("dates")["size"]
    assert page_style.style("dates")["size"] > page_style.style("place")["size"]
    assert page_style.style("dates")["color"] == "meta"
    assert page_style.style("place")["color"] == "meta"
