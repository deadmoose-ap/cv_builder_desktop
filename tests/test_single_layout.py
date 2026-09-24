"""The single-column (ATS) layout: document key, story, renderers, text layer."""
import re
from copy import deepcopy
from pathlib import Path

import pytest
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Paragraph

from cv_builder.domain import layouts
from cv_builder.domain.cv_labels import labels
from cv_builder.domain.model import example_document, new_document, normalize_document
from cv_builder.domain.themes import TEXT_DARK
from cv_builder.exporters import page_style, pdf
from cv_builder.exporters.pdf import generate_pdf
from cv_builder.exporters.preview_layout import _wrap, build_pages
from cv_builder.exporters.story import (
    INLINE_SEPARATOR,
    NBSP,
    Group,
    Para,
    main_story,
    single_column_story,
)


def _single(data=None) -> dict:
    data = normalize_document(data if data is not None else example_document())
    data["layout"] = "single"
    return data


def _paras(story) -> list[Para]:
    result = []
    for item in story:
        if isinstance(item, Group):
            result += list(item.items)
        elif isinstance(item, Para):
            result.append(item)
    return result


def _page_count(path: Path) -> int:
    return len(re.findall(rb"/Type\s*/Page[^s]", path.read_bytes()))


def test_layout_is_optional_and_always_normalized():
    assert new_document()["layout"] == layouts.DEFAULT_LAYOUT == "sidebar"
    assert example_document()["layout"] == "sidebar"

    legacy = new_document()
    del legacy["layout"]
    assert normalize_document(legacy)["layout"] == "sidebar"

    unknown = new_document()
    unknown["layout"] = "three-columns"
    assert normalize_document(unknown)["layout"] == "sidebar"

    chosen = new_document()
    chosen["layout"] = "single"
    assert normalize_document(chosen)["layout"] == "single"


def test_single_story_reads_in_ats_order():
    data = _single()
    profile = data["profile"]
    text = labels(data["locale"])
    paras = _paras(single_column_story(data))
    texts = [para.text for para in paras]

    assert texts[0] == profile["name"]
    assert texts[1] == profile["headline"]
    contact = texts[2]
    assert paras[2].style == "contact"
    for value in (profile["location"], profile["email"], profile["linkedin"], profile["telegram"]):
        assert value in contact
    assert texts[3 : 3 + len(profile["portfolio"])] == profile["portfolio"]

    headings = [para.text for para in paras if para.style == "section"]
    assert headings == [
        text["summary"],
        text["core_skills"],
        text["experience"],
        text["education"],
        text["languages"],
    ]
    # Sidebar-only headings never appear: their content moved into the flow.
    assert text["contact"] not in texts
    assert text["portfolio"] not in texts


def test_single_story_keeps_skills_on_one_line_each():
    data = _single()
    data["profile"]["skills"] = ["Data analysis", "Python", "  "]
    skills = next(para for para in _paras(single_column_story(data)) if para.style == "inline")
    assert skills.text == f"Data{NBSP}analysis{INLINE_SEPARATOR}Python"


def test_single_story_omits_empty_blocks():
    data = _single(new_document())
    data["profile"]["name"] = "Jane Doe"
    data["profile"]["email"] = "jane@example.com"
    texts = [para.text for para in _paras(single_column_story(data))]
    assert texts == ["Jane Doe", "jane@example.com"]
    assert single_column_story(_single(new_document())) == []


def test_role_and_dates_share_one_line():
    data = _single()
    position = data["experience"][0]["positions"][0]
    paras = _paras(single_column_story(data))
    role_lines = [para.text for para in paras if para.style == "role"]
    assert role_lines[0].startswith(f"{position['role']}  ·  ")
    assert "Present" in role_lines[0]
    assert not [para for para in paras if para.style == "dates" and "Present" in para.text]


def test_section_headings_are_never_left_alone_at_a_page_end():
    for item in single_column_story(_single()):
        if isinstance(item, Para):
            assert item.style != "section", item.text


def test_sidebar_story_is_unchanged_by_the_layout_key():
    sidebar = normalize_document(example_document())
    single = _single()
    assert main_story(sidebar) == main_story(single)


def test_single_layout_exports_example_and_empty_documents(tmp_path: Path):
    target = tmp_path / "ats.pdf"
    generate_pdf(_single(), target)
    assert target.read_bytes().startswith(b"%PDF-")
    assert _page_count(target) >= 1

    empty = tmp_path / "ats-empty.pdf"
    generate_pdf(_single(new_document()), empty)
    assert _page_count(empty) == 1


@pytest.mark.parametrize("layout", ["sidebar", "single"])
def test_preview_and_export_agree_at_every_length_in_both_layouts(tmp_path: Path, layout):
    base = normalize_document(example_document())
    base["layout"] = layout
    # Long enough that the non-breaking skills paragraph wraps more than once.
    base["profile"]["skills"] = [f"Skill number {index} with words" for index in range(24)]
    for count in range(1, 8):
        data = deepcopy(base)
        data["experience"] = data["experience"] * count
        target = tmp_path / f"{layout}-{count}.pdf"
        generate_pdf(data, target)
        assert len(build_pages(data)) == _page_count(target), f"{layout}, {count} companies"


def test_non_breaking_skills_wrap_like_reportlab():
    font = pdf.register_fonts("en")
    text = INLINE_SEPARATOR.join(
        f"Skill{NBSP}number{NBSP}{index}" for index in range(30)
    )
    lines = [line for _, line in _wrap(text, 10.5, page_style.SINGLE_WIDTH, 0, 0, font)]
    assert len(lines) > 1

    style = pdf._styles("#29414c", font, font, False)["inline"]
    paragraph = Paragraph(pdf._safe(text), style)
    paragraph.wrap(page_style.SINGLE_WIDTH, 1000)
    assert lines == [" ".join(line[1]) for line in paragraph.blPara.lines]
    for line in lines:
        # Every break falls right after a pipe, never inside a skill.
        assert line.endswith("|") or line == lines[-1], line
        assert pdfmetrics.stringWidth(line, font, 10.5) <= page_style.SINGLE_WIDTH + 0.5


def test_single_layout_has_no_plate_and_ignores_the_theme():
    mint = _single()
    mint["theme"] = "mint"
    ink = _single()
    ink["theme"] = "ink"
    mint_pages = build_pages(mint)
    assert [page.lines for page in mint_pages] == [page.lines for page in build_pages(ink)]
    assert all(page.layout == "single" for page in mint_pages)
    colours = {line.color for page in mint_pages for line in page.lines}
    assert colours <= set(TEXT_DARK.values())
    xs = [line.x for page in mint_pages for line in page.lines]
    assert min(xs) >= page_style.SINGLE_X


@pytest.mark.parametrize("locale", ["ja", "ru"])
def test_single_layout_localizes_and_wraps_cjk_in_both_renderers(tmp_path: Path, locale):
    data = _single()
    data["locale"] = locale
    if locale == "ja":
        data["profile"]["summary"] = [
            "十年以上にわたりプロダクトデザインに携わり、金融およびヘルスケア領域で"
            "複数のチームを率いてきました。ユーザー調査から実装までを一貫して担当しています。"
        ] * 4
    font = pdf.register_fonts(locale)
    pages = build_pages(data)
    texts = {line.text for page in pages for line in page.lines}
    assert labels(locale)["experience"] in texts
    for line in pages[0].lines:
        width = pdfmetrics.stringWidth(line.text, font, line.size)
        assert line.x + width <= page_style.SINGLE_X + page_style.SINGLE_WIDTH + 0.5, line.text

    target = tmp_path / f"{locale}.pdf"
    generate_pdf(data, target)
    assert len(pages) == _page_count(target)


@pytest.mark.parametrize("layout", ["sidebar", "single"])
def test_pdf_metadata_names_the_candidate(tmp_path: Path, layout):
    pypdf = pytest.importorskip("pypdf")
    data = normalize_document(example_document())
    data["layout"] = layout
    target = tmp_path / "meta.pdf"
    generate_pdf(data, target)
    metadata = pypdf.PdfReader(str(target)).metadata
    assert metadata.title == f"{data['profile']['name']} - CV"
    assert metadata.author == data["profile"]["name"]


def test_single_layout_text_layer_is_in_reading_order(tmp_path: Path):
    pypdf = pytest.importorskip("pypdf")
    data = _single()
    target = tmp_path / "order.pdf"
    generate_pdf(data, target)
    extracted = "\n".join(page.extract_text() for page in pypdf.PdfReader(str(target)).pages)
    lines = [line.strip() for line in extracted.replace(NBSP, " ").splitlines() if line.strip()]
    profile = data["profile"]
    text = labels(data["locale"])

    assert lines[0] == profile["name"]
    order = [
        profile["headline"],
        profile["email"],
        profile["portfolio"][0],
        text["summary"],
        text["core_skills"],
        text["experience"],
        text["education"],
        text["languages"],
    ]
    positions = [next(i for i, line in enumerate(lines) if value in line) for value in order]
    assert positions == sorted(positions), list(zip(order, positions))
