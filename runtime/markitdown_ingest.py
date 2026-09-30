"""Optional Microsoft MarkItDown ingestion boundary for Book.

Upstream: microsoft/markitdown @
b8f79c57ebc0044be41323d89b2a45d3fda8460e (MIT).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class MarkItDownIngestResult:
    source_path: str
    markdown: str
    backend: str = "markitdown"


class MarkItDownIngestor:
    """Wrap MarkItDown.convert_local() with an explicit local-file boundary."""

    def __init__(self, converter: Any) -> None:
        if not callable(getattr(converter, "convert_local", None)):
            raise TypeError("converter must provide convert_local(path)")
        self._converter = converter

    def convert_local(self, source_path: str | Path) -> MarkItDownIngestResult:
        path = Path(source_path)
        if not path.is_file():
            raise FileNotFoundError(path)
        result = self._converter.convert_local(path)
        markdown = str(getattr(result, "text_content", "") or "").strip()
        if not markdown:
            raise ValueError("MarkItDown returned empty text_content")
        return MarkItDownIngestResult(
            source_path=str(path),
            markdown=markdown,
        )


class DocumentIngestFallback:
    """Try multiple explicit local ingestors in order, preserving the winner."""

    def __init__(self, ingestors: Iterable[Any]) -> None:
        self._ingestors = list(ingestors)
        if not self._ingestors:
            raise ValueError("at least one ingestor is required")

    def convert_local(self, source_path: str | Path) -> Any:
        errors: list[str] = []
        for ingestor in self._ingestors:
            convert = getattr(ingestor, "convert_local", None)
            if not callable(convert):
                errors.append(f"{ingestor.__class__.__name__}: missing convert_local")
                continue
            try:
                return convert(source_path)
            except Exception as exc:
                errors.append(f"{ingestor.__class__.__name__}: {exc}")
        raise RuntimeError("all document ingestors failed: " + " | ".join(errors))


def create_markitdown_ingestor(**kwargs: Any) -> MarkItDownIngestor:
    try:
        from markitdown import MarkItDown
    except ImportError as exc:
        raise RuntimeError(
            "MarkItDown is optional; install requirements-extras/document.txt"
        ) from exc
    return MarkItDownIngestor(MarkItDown(**kwargs))
