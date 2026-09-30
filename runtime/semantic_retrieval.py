"""Optional sentence-transformers semantic retrieval for Book.

Upstream: huggingface/sentence-transformers @
4a3b5cd6ec718e421f57e824a41ed3fd99595df6 (Apache-2.0).

Book remains authoritative for textbook/source identity and structured content.
This module only ranks already-approved text chunks semantically.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class SemanticHit:
    document_id: str
    score: float
    text: str
    metadata: dict[str, Any]


def _vector(value: Any) -> list[float]:
    tolist = getattr(value, "tolist", None)
    if callable(tolist):
        value = tolist()
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise TypeError("embedding must be a numeric sequence")
    return [float(item) for item in value]


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b):
        raise ValueError("embedding dimensions must match")
    dot = sum(x * y for x, y in zip(a, b))
    na = sqrt(sum(x * x for x in a))
    nb = sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


class SentenceTransformerSemanticIndex:
    """In-memory semantic ranker with an injected SentenceTransformer-like model."""

    def __init__(self, model: Any) -> None:
        if not callable(getattr(model, "encode", None)):
            raise TypeError("model must provide encode()")
        self._model = model
        self._rows: list[tuple[str, str, dict[str, Any], list[float]]] = []

    def build(self, documents: Iterable[Mapping[str, Any]]) -> None:
        rows = list(documents)
        ids: list[str] = []
        texts: list[str] = []
        metadata: list[dict[str, Any]] = []
        for row in rows:
            document_id = str(row.get("document_id") or row.get("id") or "").strip()
            text = str(row.get("text") or "").strip()
            if not document_id or not text:
                raise ValueError("each document needs non-empty document_id and text")
            ids.append(document_id)
            texts.append(text)
            raw_meta = row.get("metadata", {})
            metadata.append(dict(raw_meta) if isinstance(raw_meta, Mapping) else {})
        if not texts:
            self._rows = []
            return

        embeddings = self._model.encode(
            texts,
            convert_to_numpy=False,
            normalize_embeddings=False,
        )
        if len(embeddings) != len(texts):
            raise RuntimeError("encoder returned unexpected embedding count")
        self._rows = [
            (doc_id, text, meta, _vector(embedding))
            for doc_id, text, meta, embedding in zip(ids, texts, metadata, embeddings)
        ]

    def query(self, text: str, *, limit: int = 5) -> list[SemanticHit]:
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
            raise ValueError("limit must be >= 1")
        query = str(text).strip()
        if not query or not self._rows:
            return []
        encoded = self._model.encode(
            [query],
            convert_to_numpy=False,
            normalize_embeddings=False,
        )
        query_vector = _vector(encoded[0])
        hits = [
            SemanticHit(
                document_id=document_id,
                score=round(_cosine(query_vector, embedding), 6),
                text=body,
                metadata=dict(meta),
            )
            for document_id, body, meta, embedding in self._rows
        ]
        hits.sort(key=lambda item: (-item.score, item.document_id))
        return hits[:limit]


def create_sentence_transformer_index(
    model_name_or_path: str,
    *,
    local_files_only: bool = True,
    **model_kwargs: Any,
) -> SentenceTransformerSemanticIndex:
    """Create a local-first SentenceTransformer index lazily.

    By default local_files_only=True so Book does not silently download a model.
    """
    if not str(model_name_or_path).strip():
        raise ValueError("model_name_or_path cannot be empty")
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "sentence-transformers is optional; install requirements-extras/semantic.txt"
        ) from exc
    model = SentenceTransformer(
        model_name_or_path,
        local_files_only=local_files_only,
        **model_kwargs,
    )
    return SentenceTransformerSemanticIndex(model)
