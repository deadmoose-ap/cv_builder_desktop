"""Smoke tests for the data layer and PDF renderer."""
import re
from pathlib import Path

from reportlab.pdfbase import pdfmetrics

from cv_builder.domain import cv_labels, locales, themes
from cv_builder.domain.completion import calculate_completion
from cv_builder.domain.model import (
    example_document,
    load_document,
    new_document,
    normalize_document,
    save_document,
)
from cv_builder.domain.text import split_lines, split_paragraphs
from cv_builder.exporters import page_style, pdf
from cv_builder.exporters.pdf import generate_pdf
from cv_builder.exporters.preview_layout import build_pages
from cv_builder.infrastructure.library import CVLibrary
from cv_builder.infrastructure.settings import AppSettings, SettingsStore
from cv_builder.ui.i18n import Translator
from cv_builder.ui import strings as ui_strings
from cv_builder.ui.strings import en as ui_strings_en


def test_json_round_trip(tmp_path: Path):
    target = tmp_path / "sample.json"
    original = new_document()
    save_document(target, original)
    assert load_document(target) == original


def test_pdf_generation(tmp_path: Path):
    target = tmp_path / "sample.pdf"
    generate_pdf(new_document(), target)
    assert target.read_bytes().startswith(b"%PDF-")
    assert target.stat().st_size > 10_000


def test_completion_is_explainable_and_bounded():
    starter = new_document()
    assert calculate_completion(starter) == 0

    complete = new_document()
    complete["profile"] = {
        "name": "Alex Morgan",
        "headline": "Product Designer",
        "location": "Berlin, Germany",
        "email": "alex@example.com",
        "linkedin": "linkedin.com/in/alex",
        "skills": ["Product design"],
        "summary": ["Design leader focused on useful products."],
    }
    complete["experience"] = [
        {
            "company": "Northstar Labs",
            "duration": "2 years",
            "role": "Product Designer",
            "dates": "2024 - Present",
            "place": "Berlin",
            "intro": "",
            "work": [],
            "results": [],
        }
    ]
    complete["education"] = {
        "institution": "Design University",
        "qualification": "BA Design, 2020",
    }
    assert calculate_completion(complete) == 100

    starter["profile"]["name"] = "Alex Morgan"
    assert calculate_completion(starter) == 10


def test_text_helpers_remove_empty_values():
    assert split_lines("Design\n\n Research \n") == ["Design", "Research"]
    assert split_paragraphs("First paragraph.\n\n\nSecond paragraph.") == [
        "First paragraph.",
        "Second paragraph.",
    ]


def test_example_is_separate_from_empty_new_document():
    assert new_document()["profile"]["name"] == ""
    assert new_document()["experience"] == []
    assert example_document()["profile"]["name"] == "YOUR NAME"
    assert example_document()["experience"]


def test_theme_is_optional_and_always_normalized():
    assert new_document()["theme"] == themes.DEFAULT_THEME

    legacy = new_document()
    del legacy["theme"]
    assert normalize_document(legacy)["theme"] == themes.DEFAULT_THEME

    unknown = new_document()
    unknown["theme"] = "not-a-theme"
    assert normalize_document(unknown)["theme"] == themes.DEFAULT_THEME

    chosen = new_document()
    chosen["theme"] = "mint"
    assert normalize_document(chosen)["theme"] == "mint"


def test_sidebar_text_colour_follows_plate_contrast():
    expected_dark = {"#adc178", "#c2f8cb"}
    for theme in themes.SIDEBAR_THEMES:
        uses_dark = themes.sidebar_uses_dark_text(theme["color"])
        assert uses_dark is (theme["color"] in expected_dark), theme["key"]

    assert page_style.resolve_color("side_head", "#c2f8cb") == "#0b0b0b"
    assert page_style.resolve_color("side_body", "#c2f8cb") == "#161616"
    assert page_style.resolve_color("side_body", "#020c1a") == "#ffffff"
    # Main-column text never depends on the sidebar plate.
    assert page_style.resolve_color("section", "#c2f8cb") == "#0b0b0b"
    assert page_style.resolve_color("body", "#020c1a") == "#161616"
    assert page_style.resolve_color("location", "#020c1a") == "#a9a9a9"


def test_theme_reaches_the_exported_pdf(tmp_path: Path):
    data = example_document()
    data["theme"] = "mint"
    target = tmp_path / "themed.pdf"
    generate_pdf(data, target)
    assert target.read_bytes().startswith(b"%PDF-")


def test_preview_matches_the_exported_page_count(tmp_path: Path):
    data = normalize_document(example_document())
    data["experience"] = data["experience"] * 6
    data["theme"] = "mint"

    pages = build_pages(data)
    target = tmp_path / "long.pdf"
    generate_pdf(data, target)
    exported = len(re.findall(rb"/Type\s*/Page[^s]", target.read_bytes()))
    assert len(pages) == exported > 1

    assert pages[0].sidebar_color == "#c2f8cb"
    sidebar_lines = [line for line in pages[0].lines if line.x < page_style.MAIN_X]
    assert "CONTACT" in {line.text for line in sidebar_lines}
    assert pages[0].lines[-1].text == "Page 1"
    assert all(line.color in ("#0b0b0b", "#161616") for line in sidebar_lines)
    # The contact block is printed on the first page only.
    assert all(line.x >= page_style.MAIN_X for line in pages[1].lines[:-1])
    assert pages[1].lines[-1].text == "Page 2"


def test_local_library_create_autosave_rename_import_and_delete(tmp_path: Path):
    library = CVLibrary(tmp_path / "library")
    first = library.create_document()
    second = library.create_document()
    assert first.title == "Untitled CV"
    assert second.title == "Untitled CV 2"

    data = library.load_document(first.id)
    data["profile"]["name"] = "Alex Morgan"
    updated = library.save_document(first.id, data)
    assert updated.updated_at
    assert library.load_document(first.id)["profile"]["name"] == "Alex Morgan"

    renamed = library.rename_document(first.id, "Product CV")
    assert renamed.title == "Product CV"

    exported = tmp_path / "external.json"
    save_document(exported, example_document())
    imported = library.import_document(exported)
    assert imported.title == "YOUR NAME"
    assert library.load_document(imported.id)["profile"]["headline"]

    library.delete_document(second.id)
    assert {record.id for record in library.list_documents()} == {
        first.id,
        imported.id,
    }


def test_local_library_duplicate_document(tmp_path: Path):
    library = CVLibrary(tmp_path / "library")
    source = library.create_document("Product CV", example_document())

    copy = library.duplicate_document(source.id)
    assert copy.id != source.id
    assert copy.title == "Product CV copy"
    assert library.load_document(copy.id) == library.load_document(source.id)

    second_copy = library.duplicate_document(source.id)
    assert second_copy.title == "Product CV copy 2"

    data = library.load_document(copy.id)
    data["profile"]["name"] = "Copy Only"
    library.save_document(copy.id, data)
    assert library.load_document(source.id)["profile"]["name"] != "Copy Only"

    try:
        library.duplicate_document("missing-id")
    except KeyError:
        pass
    else:
        raise AssertionError("duplicate_document must reject unknown ids")


def test_locale_is_optional_and_always_normalized():
    assert new_document()["locale"] == locales.DEFAULT_LOCALE

    legacy = new_document()
    del legacy["locale"]
    assert normalize_document(legacy)["locale"] == locales.DEFAULT_LOCALE

    unknown = new_document()
    unknown["locale"] = "kl"
    assert normalize_document(unknown)["locale"] == locales.DEFAULT_LOCALE

    chosen = new_document()
    chosen["locale"] = "ja"
    assert normalize_document(chosen)["locale"] == "ja"


def test_cv_labels_cover_every_locale():
    expected = set(cv_labels.LABELS["en"])
    for code in locales.LOCALE_CODES:
        headings = cv_labels.LABELS[code]
        assert set(headings) == expected, code
        assert all(value.strip() for value in headings.values()), code
        # Every locale must number its pages, and must do so with the number.
        assert cv_labels.page_label(code, 2).strip() != ""
        assert "2" in cv_labels.page_label(code, 2)
    # An unknown locale falls back rather than raising mid-export.
    assert cv_labels.labels("kl") is cv_labels.LABELS["en"]


def test_ui_strings_have_identical_keys():
    # Registered statically, so PyInstaller keeps them: a dynamic import here
    # once passed every test from source and crashed the built .app.
    assert set(ui_strings.STRINGS_BY_LOCALE) == set(locales.LOCALE_CODES)

    expected = set(ui_strings_en.STRINGS)
    for code in locales.LOCALE_CODES:
        strings = Translator(code)._strings
        assert set(strings) == expected, code
        assert all(value.strip() for value in strings.values()), code
    # A missing key degrades to the key itself instead of crashing a window.
    assert Translator("ru")("no.such.key") == "no.such.key"
    assert Translator("ru")("status.progress", percent=7) == "Заполнено на 7%"


def test_every_cjk_locale_has_a_font_with_glyphs(tmp_path: Path):
    assert set(pdf.CJK_FONTS) == set(locales.CJK_LOCALES)
    samples = {
        "ja": "経験あア",
        "ko": "경력한글",
        "zh-Hans": "工作经验简",
        "zh-Hant": "工作經驗繁",
    }
    for code, sample in samples.items():
        font_name = pdf.register_fonts(code)
        assert font_name == pdf.font_for_locale(code), code
        face = pdfmetrics.getFont(font_name).face
        missing = [char for char in sample if ord(char) not in face.charToGlyph]
        assert not missing, f"{code} font cannot draw {missing}"

        data = normalize_document(example_document())
        data["locale"] = code
        data["profile"]["name"] = sample
        target = tmp_path / f"{code}.pdf"
        generate_pdf(data, target)
        assert target.read_bytes().startswith(b"%PDF-")
        assert target.stat().st_size > 10_000


def test_cjk_text_wraps_inside_the_column_in_both_renderers(tmp_path: Path):
    # Japanese has no spaces: word-level wrapping would run one paragraph far
    # past the page edge, so both renderers must break between characters.
    paragraph = (
        "十年以上にわたりプロダクトデザインに携わり、金融およびヘルスケア領域で"
        "複数のチームを率いてきました。ユーザー調査から実装までを一貫して担当しています。"
    )
    data = normalize_document(example_document())
    data["locale"] = "ja"
    data["profile"]["summary"] = [paragraph] * 4

    font = pdf.register_fonts("ja")
    pages = build_pages(data)
    body = [line for line in pages[0].lines if line.x >= page_style.MAIN_X]
    assert body
    for line in body:
        width = pdfmetrics.stringWidth(line.text, font, line.size)
        assert width <= page_style.MAIN_WIDTH + 0.5, line.text

    target = tmp_path / "japanese.pdf"
    generate_pdf(data, target)
    exported = len(re.findall(rb"/Type\s*/Page[^s]", target.read_bytes()))
    assert len(pages) == exported


def test_localized_headings_reach_both_renderers(tmp_path: Path):
    data = normalize_document(example_document())
    data["locale"] = "ru"

    pages = build_pages(data)
    sidebar = {
        line.text for line in pages[0].lines if line.x < page_style.MAIN_X
    }
    assert "КОНТАКТЫ" in sidebar
    assert "CONTACT" not in sidebar
    assert pages[0].lines[-1].text == "Стр. 1"
    assert "ОПЫТ РАБОТЫ" in {line.text for line in pages[0].lines}

    # The same document still paginates identically once exported.
    target = tmp_path / "russian.pdf"
    generate_pdf(data, target)
    exported = len(re.findall(rb"/Type\s*/Page[^s]", target.read_bytes()))
    assert len(pages) == exported


def test_settings_round_trip_and_survive_a_corrupt_file(tmp_path: Path):
    store = SettingsStore(tmp_path / "settings")
    assert store.load().ui_locale == "en"

    assert store.set_ui_locale("ja").ui_locale == "ja"
    assert SettingsStore(tmp_path / "settings").load().ui_locale == "ja"

    # An unsupported or unreadable value must not stop the app from starting.
    store.save(AppSettings(ui_locale="kl"))
    assert store.load().ui_locale == "en"
    store.path.write_text("{not json", encoding="utf-8")
    assert store.load().ui_locale == "en"
