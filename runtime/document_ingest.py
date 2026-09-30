"""Unified local document-ingest staging pipeline.

Primary upstream: docling-project/docling @
d6f03078ad364108df3e7e82e8f0dcc3fd7f39ea (MIT).

Docling is tried first for high-fidelity structure; MarkItDown remains the
fallback. The result is staging data only and never mutates Book canonical
structures automatically.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Any, Iterable

from .docling_ingest import create_docling_ingestor
from .markitdown_ingest import create_markitdown_ingestor


@dataclass(frozen=True)
class DocumentIngestResult:
    source_path: str
    source_sha256: str
    markdown: str
    backend: str

    def manifest(self) -> dict[str, str]:
        return {
            "source_path": self.source_path,
            "source_sha256": self.source_sha256,
            "backend": self.backend,
        }


class DocumentIngestPipeline:
    """Ordered local-file ingestion with normalized staging output."""

    def __init__(self, ingestors: Iterable[Any]) -> None:
        self._ingestors = list(ingestors)
        if not self._ingestors:
            raise ValueError("at least one document ingestor is required")

    def convert_local(self, source_path: str | Path) -> DocumentIngestResult:
        path = Path(source_path)
        if not path.is_file():
            raise FileNotFoundError(path)
        source_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        failures: list[str] = []
        for ingestor in self._ingestors:
            convert = getattr(ingestor, "convert_local", None)
            if not callable(convert):
                failures.append(f"{ingestor.__class__.__name__}:missing-convert_local")
                continue
            try:
                result = convert(path)
                markdown = str(getattr(result, "markdown", "") or "").strip()
                backend = str(getattr(result, "backend", ingestor.__class__.__name__) or "").strip()
                if not markdown:
                    raise ValueError("empty markdown")
                return DocumentIngestResult(
                    source_path=str(path),
                    source_sha256=source_sha256,
                    markdown=markdown,
                    backend=backend,
                )
            except Exception as exc:
                failures.append(f"{ingestor.__class__.__name__}:{exc.__class__.__name__}")
        raise RuntimeError("all document ingestors failed: " + ", ".join(failures))


def create_document_ingest_pipeline() -> DocumentIngestPipeline:
    """Build the installed local ingest chain without downloading anything."""
    ingestors: list[Any] = []
    try:
        ingestors.append(create_docling_ingestor())
    except RuntimeError:
        pass
    try:
        ingestors.append(create_markitdown_ingestor())
    except RuntimeError:
        pass
    if not ingestors:
        raise RuntimeError(
            "no document ingestor is installed; install requirements-extras/document.txt"
        )
    return DocumentIngestPipeline(ingestors)
