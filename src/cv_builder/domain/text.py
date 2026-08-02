"""Turn free-form editor text into the lists the document schema expects."""
from __future__ import annotations


def split_paragraphs(value: str) -> list[str]:
    """Split on blank lines; empty paragraphs are dropped."""
    return [part.strip() for part in value.split("\n\n") if part.strip()]


def split_lines(value: str) -> list[str]:
    """One item per non-empty line."""
    return [line.strip() for line in value.splitlines() if line.strip()]
