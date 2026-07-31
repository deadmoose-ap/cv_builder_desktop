"""Smoke tests for the data layer and PDF renderer."""
from pathlib import Path

from app import calculate_completion, split_lines, split_paragraphs
from cv_library import CVLibrary
from cv_model import example_document, load_document, new_document, save_document
from pdf_generator import generate_pdf


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
