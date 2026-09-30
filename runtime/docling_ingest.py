"""Optional Docling document ingestion boundary for Book.

Upstream: docling-project/docling @
d6f03078ad364108df3e7e82e8f0dcc3fd7f39ea (MIT).

This module converts an explicitly supplied local source file into markdown.
It does not mutate canonical textbook structures automatically.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DoclingIngestResult:
    source_path: str
    markdown: str
    backend: str = "docling"


class DoclingIngestor:
    """Wrap DocumentConverter.convert() + document.export_to_markdown()."""

    def __init__(self, converter: Any) -> None:
        if not callable(getattr(converter, "convert", None)):
            raise TypeError("converter must provide convert(source)")
        self._converter = converter

    def convert_local(self, source_path: str | Path) -> DoclingIngestResult:
        path = Path(source_path)
        if not path.is_file():
            raise FileNotFoundError(path)
        result = self._converter.convert(path)
        document = getattr(result, "document", None)
        export = getattr(document, "export_to_markdown", None)
        if not callable(export):
            raise TypeError("Docling conversion result must expose document.export_to_markdown()")
        markdown = str(export()).strip()
        if not markdown:
            raise ValueError("Docling returned empty markdown")
        return DoclingIngestResult(
            source_path=str(path),
            markdown=markdown,
        )


def create_docling_ingestor(**converter_kwargs: Any) -> DoclingIngestor:
    """Create Docling lazily; no document is converted until explicitly requested."""
    try:
        from docling.document_converter import DocumentConverter
    except ImportError as exc:
        raise RuntimeError(
            "Docling is optional; install requirements-extras/document.txt before enabling ingestion"
        ) from exc
    return DoclingIngestor(DocumentConverter(**converter_kwargs))
