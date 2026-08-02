"""Use cases the UI triggers: library commands, autosave and exports.

Every path that touches the filesystem or an output format goes through this
service, so no screen ever calls `json.dump`, `save_document` or `generate_pdf`
directly.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from cv_builder.domain.model import example_document, new_document, save_document
from cv_builder.exporters.pdf import generate_pdf
from cv_builder.infrastructure.library import CVLibrary, CVRecord


class DocumentService:
    """Thin orchestration layer between the UI and storage/exporters."""

    def __init__(self, library: CVLibrary | None = None):
        self.library = library or CVLibrary()

    # --- library ---------------------------------------------------------

    def list_documents(self) -> list[CVRecord]:
        return self.library.list_documents()

    def get_record(self, document_id: str) -> CVRecord:
        return self.library.get_record(document_id)

    def load(self, document_id: str) -> dict[str, Any]:
        return self.library.load_document(document_id)

    def create(self, locale: str | None = None) -> CVRecord:
        """Create an empty CV, optionally pre-set to a language.

        The domain default stays `en`; picking up the interface language is an
        application-level convenience, so `domain.model` stays unaware of any
        application setting.
        """
        document = new_document()
        if locale:
            document["locale"] = locale
        return self.library.create_document(data=document)

    def duplicate(self, document_id: str) -> CVRecord:
        return self.library.duplicate_document(document_id)

    def rename(self, document_id: str, title: str) -> CVRecord:
        return self.library.rename_document(document_id, title)

    def delete(self, document_id: str) -> None:
        self.library.delete_document(document_id)

    def save(self, document_id: str, data: dict[str, Any]) -> CVRecord:
        return self.library.save_document(document_id, data)

    def new_document(self) -> dict[str, Any]:
        return new_document()

    # --- import / export -------------------------------------------------

    def import_json(self, path: str | Path) -> CVRecord:
        return self.library.import_document(path)

    def export_json(self, path: str | Path, data: dict[str, Any]) -> None:
        save_document(path, data)

    def export_example_json(self, path: str | Path) -> None:
        save_document(path, example_document())

    def export_pdf(self, path: str | Path, data: dict[str, Any]) -> None:
        generate_pdf(data, path)
