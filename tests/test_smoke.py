"""Smoke tests for the data layer and PDF renderer."""
import re
from copy import deepcopy
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Paragraph

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
from cv_builder.exporters.preview_layout import _wrap, build_pages
from cv_builder.exporters.story import sidebar_story
from cv_builder.infrastructure.library import CVLibrary
from cv_builder.infrastructure.settings import AppSettings, SettingsStore
from cv_builder.ui.i18n import Translator
from cv_builder.ui import strings as ui_strings
from cv_builder.ui.strings import en as ui_strings_en


def _paragraph_line_texts(paragraph: Paragraph) -> list[str]:
    """Extract ReportLab line text from both tuple and FragLine layouts."""
    lines = []
    for line in paragraph.blPara.lines:
        words = line.words if hasattr(line, "words") else line[1]
        if words and isinstance(words[0], str):
            lines.append(" ".join(words))
        else:
            lines.append("".join(getattr(fragment, "text", "") for fragment in words))
    return lines


def test_json_round_trip(tmp_path: Path):
    target = tmp_path / "sample.json"
    original = new_document()
    save_document(target, original)
    assert load_document(target) == original


def test_pdf_generation(tmp_path: Path):
    target = tmp_path / "sample.pdf"
    generate_pdf(example_document(), target)
    assert target.read_bytes().startswith(b"%PDF-")
    assert target.stat().st_size > 10_000
    assert len(re.findall(rb"/Type\s*/Page[^s]", target.read_bytes())) > 0


def test_empty_document_exports_one_page(tmp_path: Path):
    target = tmp_path / "empty.pdf"
    generate_pdf(new_document(), target)
    assert target.read_bytes().startswith(b"%PDF-")
    assert len(re.findall(rb"/Type\s*/Page[^s]", target.read_bytes())) == 1


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
    assert all(line.color in ("#0b0b0b", "#161616") for line in sidebar_lines)
    assert all("Page " not in line.text for page in pages for line in page.lines)
    # The contact block is printed on the first page only.
    assert all(line.x >= page_style.MAIN_X for line in pages[1].lines)


def test_preview_and_export_agree_at_every_length(tmp_path: Path):
    """Guards the spacing rules, not just one lucky document length.

    Page breaks are the one place the two renderers can silently drift, and a
    single fixture only ever exercises one position in the column.
    """
    base = normalize_document(example_document())
    for count in range(1, 8):
        data = deepcopy(base)
        data["experience"] = data["experience"] * count
        target = tmp_path / f"length-{count}.pdf"
        generate_pdf(data, target)
        exported = len(re.findall(rb"/Type\s*/Page[^s]", target.read_bytes()))
        assert len(build_pages(data)) == exported, f"{count} companies"


def test_the_sidebar_orders_optional_blocks_and_uses_bullets():
    data = normalize_document(example_document())
    data["locale"] = "ru"
    texts = [item.text for item in sidebar_story(data) if hasattr(item, "text")]
    assert texts.index("КОНТАКТЫ") < texts.index("ПОРТФОЛИО")
    assert texts.index("ПОРТФОЛИО") < texts.index("ЯЗЫКИ")
    assert texts.index("ЯЗЫКИ") < texts.index("КЛЮЧЕВЫЕ НАВЫКИ")
    assert "• English - C1" in texts
    assert "• Spanish - B2" in texts
    assert "• https://your-portfolio.com" in texts
    assert "English - C1\nSpanish - B2" not in texts

    # An empty list prints no heading rather than an empty block.
    data["profile"]["languages"] = []
    empty = [item.text for item in sidebar_story(data) if hasattr(item, "text")]
    assert "ЯЗЫКИ" not in empty


def test_optional_profile_fields_normalize_without_a_schema_bump():
    legacy = new_document()
    del legacy["profile"]["telegram"]
    del legacy["profile"]["portfolio"]
    normalized = normalize_document(legacy)
    assert normalized["schema_version"] == legacy["schema_version"]
    assert normalized["profile"]["telegram"] == ""
    assert normalized["profile"]["portfolio"] == []

    imported = deepcopy(legacy)
    imported["profile"]["telegram"] = 12345
    imported["profile"]["portfolio"] = ["https://example.com", 42]
    normalized = normalize_document(imported)
    assert normalized["profile"]["telegram"] == "12345"
    assert normalized["profile"]["portfolio"] == ["https://example.com", "42"]

    assert calculate_completion(normalized) == calculate_completion(legacy)


def test_sidebar_omits_empty_optional_blocks_and_keeps_contact_plain():
    data = new_document()
    data["profile"]["telegram"] = "t.me/alex"
    items = [item for item in sidebar_story(data) if hasattr(item, "text")]
    assert [item.text for item in items] == ["CONTACT", "t.me/alex"]
    assert all(not item.text.startswith("• ") for item in items[1:])


def test_sidebar_geometry_and_long_url_wrap_match_reportlab(tmp_path: Path):
    assert page_style.SIDEBAR_WIDTH == 176
    assert page_style.MAIN_X == 197
    assert page_style.MAIN_WIDTH == 381
    assert page_style.style("side_body")["size"] == 9.5
    assert page_style.style("side_head")["bold"] is True

    url = "https://example.com/" + "very-long-path-" * 12 + "?utm_source=example&utm_medium=profile"
    data = new_document()
    data["profile"].update(
        {
            "name": "Alex Morgan",
            "headline": "Product Designer",
            "summary": [url],
            "portfolio": [url],
        }
    )
    pages = build_pages(data)
    sidebar_url = next(item.text for item in sidebar_story(data) if getattr(item, "text", "").startswith("• "))
    expected = _wrap(
        sidebar_url,
        page_style.style("side_bullet")["size"],
        page_style.SIDEBAR_TEXT_WIDTH,
        page_style.style("side_bullet")["left_indent"],
        page_style.style("side_bullet")["first_line_indent"],
        pdf.register_fonts(data["locale"]),
    )
    preview = [
        line.text
        for line in pages[0].lines
        if line.x < page_style.MAIN_X and line.text in {value for _, value in expected}
    ]
    assert preview == [value for _, value in expected]

    styles = pdf._styles("#29414c", pdf.register_fonts("en"), pdf.register_fonts("en"), False)
    paragraph = Paragraph(pdf._safe(sidebar_url), styles["side_bullet"])
    paragraph.wrap(page_style.SIDEBAR_TEXT_WIDTH, 800)
    reportlab_lines = _paragraph_line_texts(paragraph)
    assert reportlab_lines == [value for _, value in expected]

    target = tmp_path / "long-url.pdf"
    generate_pdf(data, target)
    exported = len(re.findall(rb"/Type\s*/Page[^s]", target.read_bytes()))
    assert len(pages) == exported


def test_preview_wrap_does_not_split_regular_words(tmp_path: Path):
    data = new_document()
    data["profile"].update(
        {
            "name": "Alex Morgan",
            "headline": "Product Designer",
            "summary": [("A normal word sequence " * 80).strip()],
        }
    )
    font = pdf.register_fonts(data["locale"])
    text = data["profile"]["summary"][0]
    expected = _wrap(
        text,
        page_style.style("body")["size"],
        page_style.MAIN_WIDTH,
        page_style.style("body")["left_indent"],
        page_style.style("body")["first_line_indent"],
        font,
    )
    styles = pdf._styles("#29414c", font, font, False)
    paragraph = Paragraph(pdf._safe(text), styles["body"])
    paragraph.wrap(page_style.MAIN_WIDTH, 800)
    reportlab_lines = _paragraph_line_texts(paragraph)
    assert reportlab_lines == [value for _, value in expected]

    target = tmp_path / "regular-words.pdf"
    generate_pdf(data, target)
    exported = len(re.findall(rb"/Type\s*/Page[^s]", target.read_bytes()))
    assert len(build_pages(data)) == exported


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
        assert "page" not in headings
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
    assert all("Стр." not in line.text for line in pages[0].lines)
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


def test_library_manual_order_sorting_and_v1_migration(tmp_path: Path):
    import json

    library = CVLibrary(tmp_path / "library")
    first = library.create_document("beta")
    second = library.create_document("Alpha")
    third = library.create_document("gamma")
    # New CVs open the manual order.
    assert [r.id for r in library.list_documents()] == [third.id, second.id, first.id]
    assert [r.title for r in library.list_documents("title")] == ["Alpha", "beta", "gamma"]

    library.reorder_documents([first.id, third.id, "unknown"])
    assert [r.id for r in library.list_documents()] == [first.id, third.id, second.id]

    # Saving a CV never moves it in the manual order.
    library.save_document(second.id, library.load_document(second.id))
    assert library.list_documents()[2].id == second.id

    # A version 1 index is seeded with the date order it used to show.
    index = json.loads(library.index_path.read_text(encoding="utf-8"))
    index["version"] = 1
    index["documents"][0]["updated_at"] = "2000-01-01T00:00:00+00:00"
    library.index_path.write_text(json.dumps(index), encoding="utf-8")
    assert library.list_documents()[-1].id == first.id
    assert json.loads(library.index_path.read_text(encoding="utf-8"))["version"] == 2


def test_library_sort_setting_is_validated(tmp_path: Path):
    from cv_builder.infrastructure.settings import SettingsStore

    store = SettingsStore(tmp_path)
    assert store.load().library_sort == "manual"
    assert store.set_library_sort("title").library_sort == "title"
    assert store.load().library_sort == "title"
    store.path.write_text('{"library_sort": "bogus"}', encoding="utf-8")
    assert store.load().library_sort == "manual"
