"""Hybrid keyword + semantic retrieval for Book."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class HybridHit:
    source_id: str
    score: float
    keyword_rank: int | None
    semantic_rank: int | None
    payload: Any


class HybridSearch:
    """Fuse audited keyword results with semantic hits using reciprocal-rank fusion."""

    def __init__(
        self,
        keyword_runtime: Any,
        semantic_index: Any,
        *,
        rrf_k: int = 60,
    ) -> None:
        if not callable(getattr(keyword_runtime, "search", None)):
            raise TypeError("keyword_runtime must provide search()")
        if not callable(getattr(semantic_index, "query", None)):
            raise TypeError("semantic_index must provide query()")
        if rrf_k < 1:
            raise ValueError("rrf_k must be >= 1")
        self._keyword = keyword_runtime
        self._semantic = semantic_index
        self.rrf_k = rrf_k

    def search(self, query: str, *, limit: int = 10, section_id: str | None = None) -> list[HybridHit]:
        if limit < 1:
            raise ValueError("limit must be >= 1")
        fetch_limit = min(100, max(limit * 3, 10))
        keyword = self._keyword.search(query, limit=fetch_limit, section_id=section_id)
        semantic = self._semantic.query(query, limit=fetch_limit)

        rows: dict[str, dict[str, Any]] = {}
        for rank, hit in enumerate(keyword, start=1):
            source_id = str(getattr(hit, "source_id", ""))
            if not source_id:
                continue
            row = rows.setdefault(source_id, {"score": 0.0, "keyword_rank": None, "semantic_rank": None, "payload": hit})
            row["score"] += 1.0 / (self.rrf_k + rank)
            row["keyword_rank"] = rank

        for rank, hit in enumerate(semantic, start=1):
            source_id = str(getattr(hit, "document_id", ""))
            if not source_id:
                continue
            row = rows.setdefault(source_id, {"score": 0.0, "keyword_rank": None, "semantic_rank": None, "payload": hit})
            row["score"] += 1.0 / (self.rrf_k + rank)
            row["semantic_rank"] = rank

        result = [
            HybridHit(
                source_id=source_id,
                score=round(row["score"], 8),
                keyword_rank=row["keyword_rank"],
                semantic_rank=row["semantic_rank"],
                payload=row["payload"],
            )
            for source_id, row in rows.items()
        ]
        result.sort(key=lambda item: (-item.score, item.source_id))
        return result[:limit]
