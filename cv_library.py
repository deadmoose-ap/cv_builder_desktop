"""Private, app-managed storage for CV Builder documents."""
from __future__ import annotations

import json
import os
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cv_model import load_document, new_document, normalize_document, save_document


def application_data_dir() -> Path:
    """Return the platform-native writable application data directory."""
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "CV Builder"
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return base / "CV Builder"
    base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "cv-builder"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class CVRecord:
    id: str
    title: str
    created_at: str
    updated_at: str


class CVLibrary:
    """Manage readable JSON CVs and a small metadata index."""

    def __init__(self, root: str | Path | None = None):
        self.root = Path(root) if root else application_data_dir()
        self.documents_dir = self.root / "documents"
        self.index_path = self.root / "library.json"
        self.documents_dir.mkdir(parents=True, exist_ok=True)

    def _read_index(self) -> dict[str, Any]:
        if not self.index_path.exists():
            return {"version": 1, "documents": []}
        try:
            with self.index_path.open("r", encoding="utf-8") as stream:
                index = json.load(stream)
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"Could not read the CV library: {error}") from error
        if not isinstance(index, dict) or not isinstance(index.get("documents"), list):
            raise ValueError("The CV library index is invalid.")
        return index

    def _write_index(self, index: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        temporary = self.index_path.with_suffix(".json.tmp")
        with temporary.open("w", encoding="utf-8") as stream:
            json.dump(index, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        temporary.replace(self.index_path)

    def _document_path(self, document_id: str) -> Path:
        return self.documents_dir / f"{document_id}.json"

    def _record_from_dict(self, item: dict[str, Any]) -> CVRecord:
        return CVRecord(
            id=str(item["id"]),
            title=str(item.get("title") or "Untitled CV"),
            created_at=str(item.get("created_at") or ""),
            updated_at=str(item.get("updated_at") or ""),
        )

    def list_documents(self) -> list[CVRecord]:
        index = self._read_index()
        existing = [
            item
            for item in index["documents"]
            if self._document_path(str(item.get("id", ""))).exists()
        ]
        if len(existing) != len(index["documents"]):
            index["documents"] = existing
            self._write_index(index)
        records = [self._record_from_dict(item) for item in existing]
        return sorted(records, key=lambda record: record.updated_at, reverse=True)

    def _unique_title(self, requested: str) -> str:
        base = requested.strip() or "Untitled CV"
        existing = {record.title.casefold() for record in self.list_documents()}
        if base.casefold() not in existing:
            return base
        number = 2
        while f"{base} {number}".casefold() in existing:
            number += 1
        return f"{base} {number}"

    def create_document(
        self,
        title: str = "Untitled CV",
        data: dict[str, Any] | None = None,
    ) -> CVRecord:
        index = self._read_index()
        document_id = uuid.uuid4().hex
        timestamp = utc_now()
        item = {
            "id": document_id,
            "title": self._unique_title(title),
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        save_document(self._document_path(document_id), data or new_document())
        index["documents"].append(item)
        self._write_index(index)
        return self._record_from_dict(item)

    def duplicate_document(self, document_id: str) -> CVRecord:
        """Create an independent copy of an existing CV, including its data."""
        record = self.get_record(document_id)
        data = self.load_document(document_id)
        return self.create_document(f"{record.title} copy", data)

    def get_record(self, document_id: str) -> CVRecord:
        for record in self.list_documents():
            if record.id == document_id:
                return record
        raise KeyError(f"Unknown CV: {document_id}")

    def load_document(self, document_id: str) -> dict[str, Any]:
        self.get_record(document_id)
        return load_document(self._document_path(document_id))

    def save_document(
        self,
        document_id: str,
        data: dict[str, Any],
    ) -> CVRecord:
        normalized = normalize_document(data)
        index = self._read_index()
        target = next(
            (item for item in index["documents"] if item.get("id") == document_id),
            None,
        )
        if target is None:
            raise KeyError(f"Unknown CV: {document_id}")
        save_document(self._document_path(document_id), normalized)
        target["updated_at"] = utc_now()
        self._write_index(index)
        return self._record_from_dict(target)

    def rename_document(self, document_id: str, title: str) -> CVRecord:
        clean_title = title.strip()
        if not clean_title:
            raise ValueError("CV name cannot be empty.")
        index = self._read_index()
        target = next(
            (item for item in index["documents"] if item.get("id") == document_id),
            None,
        )
        if target is None:
            raise KeyError(f"Unknown CV: {document_id}")
        target["title"] = clean_title
        target["updated_at"] = utc_now()
        self._write_index(index)
        return self._record_from_dict(target)

    def delete_document(self, document_id: str) -> None:
        index = self._read_index()
        before = len(index["documents"])
        index["documents"] = [
            item for item in index["documents"] if item.get("id") != document_id
        ]
        if len(index["documents"]) == before:
            raise KeyError(f"Unknown CV: {document_id}")
        self._write_index(index)
        path = self._document_path(document_id)
        if path.exists():
            path.unlink()

    def import_document(self, path: str | Path) -> CVRecord:
        source = Path(path)
        data = load_document(source)
        suggested_title = str(data["profile"].get("name") or source.stem)
        return self.create_document(suggested_title, data)
