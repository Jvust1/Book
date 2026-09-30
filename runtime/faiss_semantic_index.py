"""Optional FAISS acceleration for Book semantic retrieval.

Upstream: facebookresearch/faiss @
88a28bcd80aa4469bd15520c510186c98f51d985 (MIT).

This index accelerates ranking of already-approved textbook chunks. Source
identity, provenance and citation authority remain owned by Book.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from .semantic_retrieval import SemanticHit, _vector


class FaissSemanticIndex:
    """Sentence-encoder + FAISS inner-product index behind Book's hit contract."""

    def __init__(
        self,
        model: Any,
        *,
        faiss_module: Any | None = None,
        array_factory: Any | None = None,
    ) -> None:
        if not callable(getattr(model, "encode", None)):
            raise TypeError("model must provide encode()")
        if faiss_module is None:
            try:
                import faiss as faiss_module
            except ImportError as exc:
                raise RuntimeError(
                    "FAISS is optional; install requirements-extras/semantic.txt"
                ) from exc
        if array_factory is None:
            try:
                import numpy as np
            except ImportError as exc:
                raise RuntimeError(
                    "numpy is required for the optional FAISS semantic index"
                ) from exc
            array_factory = lambda rows: np.asarray(rows, dtype="float32")
        if not callable(getattr(faiss_module, "IndexFlatIP", None)):
            raise TypeError("faiss_module must provide IndexFlatIP")
        if not callable(getattr(faiss_module, "normalize_L2", None)):
            raise TypeError("faiss_module must provide normalize_L2")
        if not callable(array_factory):
            raise TypeError("array_factory must be callable")

        self._model = model
        self._faiss = faiss_module
        self._array_factory = array_factory
        self._rows: list[tuple[str, str, dict[str, Any]]] = []
        self._index: Any | None = None

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
            self._index = None
            return

        encoded = self._model.encode(
            texts,
            convert_to_numpy=False,
            normalize_embeddings=False,
        )
        if len(encoded) != len(texts):
            raise RuntimeError("encoder returned unexpected embedding count")
        vectors = [_vector(item) for item in encoded]
        dimension = len(vectors[0])
        if dimension < 1 or any(len(item) != dimension for item in vectors):
            raise ValueError("all embeddings must have the same positive dimension")

        matrix = self._array_factory(vectors)
        self._faiss.normalize_L2(matrix)
        index = self._faiss.IndexFlatIP(dimension)
        index.add(matrix)

        self._rows = list(zip(ids, texts, metadata))
        self._index = index

    def query(self, text: str, *, limit: int = 5) -> list[SemanticHit]:
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
            raise ValueError("limit must be >= 1")
        query = str(text).strip()
        if not query or self._index is None or not self._rows:
            return []

        encoded = self._model.encode(
            [query],
            convert_to_numpy=False,
            normalize_embeddings=False,
        )
        if len(encoded) != 1:
            raise RuntimeError("encoder returned unexpected query embedding count")
        matrix = self._array_factory([_vector(encoded[0])])
        self._faiss.normalize_L2(matrix)
        count = min(limit, len(self._rows))
        distances, indices = self._index.search(matrix, count)

        result: list[SemanticHit] = []
        for score, raw_index in zip(distances[0], indices[0]):
            index = int(raw_index)
            if index < 0 or index >= len(self._rows):
                continue
            document_id, body, meta = self._rows[index]
            result.append(
                SemanticHit(
                    document_id=document_id,
                    score=round(float(score), 6),
                    text=body,
                    metadata=dict(meta),
                )
            )
        return result


def create_faiss_semantic_index(
    model_name_or_path: str,
    *,
    local_files_only: bool = True,
    **model_kwargs: Any,
) -> FaissSemanticIndex:
    """Create local-first SentenceTransformer + FAISS retrieval lazily."""
    if not str(model_name_or_path).strip():
        raise ValueError("model_name_or_path cannot be empty")
    try:
        import faiss
        import numpy as np
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "FAISS semantic retrieval is optional; install requirements-extras/semantic.txt"
        ) from exc

    model = SentenceTransformer(
        model_name_or_path,
        local_files_only=local_files_only,
        **model_kwargs,
    )
    return FaissSemanticIndex(
        model,
        faiss_module=faiss,
        array_factory=lambda rows: np.asarray(rows, dtype="float32"),
    )
