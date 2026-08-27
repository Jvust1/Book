"""Platform-neutral reference loader for Book Course OS textbook assets.

The runtime consumes the repository contract documented in
``docs/RUNTIME_IMPORT_CONTRACT.md``.  It deliberately refuses to expose a
textbook as a production learning source while ``RUNTIME_READINESS`` is not
READY.

This module uses only Python's standard library.  It is a reference data layer:
web/mobile/desktop clients can either call it through a service or port the same
normalization rules to their native stack.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator


class BookRuntimeError(RuntimeError):
    """Base error for textbook runtime loading."""


class BookRuntimeBlockedError(BookRuntimeError):
    """Raised when a structured book is not yet RUNTIME_READY."""

    def __init__(self, root: Path, readiness: dict[str, Any]):
        self.root = root
        self.readiness = readiness
        missing = readiness.get("missing_required_files") or []
        stale = readiness.get("stale_files") or []
        pieces = [f"runtime status={readiness.get('status', 'UNKNOWN')}"]
        if missing:
            pieces.append("missing=" + ", ".join(map(str, missing)))
        if stale:
            pieces.append("stale=" + ", ".join(map(str, stale)))
        super().__init__(f"Book runtime blocked for {root}: " + "; ".join(pieces))


@dataclass(frozen=True)
class RuntimeAnchor:
    pdf_page: int | None = None
    printed_page: int | str | None = None
    source_anchor: str | None = None


@dataclass
class RuntimeSection:
    id: str
    number: str | None = None
    title_en: str | None = None
    title_zh: str | None = None
    chapter_id: str | None = None
    pdf_page_start: int | None = None
    pdf_page_end: int | None = None
    printed_page_start: int | str | None = None
    printed_page_end: int | str | None = None
    source_batches: list[str] = field(default_factory=list)
    continued_from: str | None = None
    continues_in: str | None = None

    def covers_pdf_page(self, page: int) -> bool:
        if self.pdf_page_start is None:
            return False
        end = self.pdf_page_end if self.pdf_page_end is not None else self.pdf_page_start
        return self.pdf_page_start <= page <= end


@dataclass
class RuntimeObject:
    id: str
    type: str
    chapter_id: str | None = None
    section_id: str | None = None
    number: str | None = None
    name_en: str | None = None
    name_zh: str | None = None
    formula: str | None = None
    anchor: RuntimeAnchor = field(default_factory=RuntimeAnchor)
    source_batch: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class RuntimeFigure:
    id: str
    title_en: str | None = None
    title_zh: str | None = None
    anchor: RuntimeAnchor = field(default_factory=RuntimeAnchor)
    source_batch: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class RuntimeBatch:
    id: str
    source_file: Path
    translation_file: Path | None
    chapter_ids: set[str] = field(default_factory=set)
    pdf_page_start: int | None = None
    pdf_page_end: int | None = None
    printed_page_start: int | str | None = None
    printed_page_end: int | str | None = None
    sections: list[RuntimeSection] = field(default_factory=list)
    objects: list[RuntimeObject] = field(default_factory=list)
    figures: list[RuntimeFigure] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


class BookRuntime:
    """Normalized read-only view of one structured textbook.

    Use ``BookRuntime.open(path)`` for production behavior.  It enforces the
    readiness gate.  ``allow_blocked=True`` exists only for diagnostics and
    recovery tooling; product learning screens should never use it.
    """

    def __init__(self, root: Path):
        self.root = root
        self.readiness: dict[str, Any] = {}
        self.completion: dict[str, Any] = {}
        self.metadata: dict[str, Any] = {}
        self.qa_policy: dict[str, Any] = {}
        self.toc: Any = None
        self.page_map: list[dict[str, str]] = []
        self.batches: list[RuntimeBatch] = []
        self.sections: dict[str, RuntimeSection] = {}
        self.objects: dict[str, RuntimeObject] = {}
        self.figures: dict[str, RuntimeFigure] = {}
        self.search_index_path: Path | None = None

    @classmethod
    def open(cls, root: str | Path, *, allow_blocked: bool = False) -> "BookRuntime":
        runtime = cls(Path(root))
        runtime._load(allow_blocked=allow_blocked)
        return runtime

    @property
    def book_id(self) -> str:
        return str(self.metadata.get("book_id") or self.completion.get("book_id") or "")

    @property
    def structured_version(self) -> str | None:
        value = self.completion.get("version")
        return str(value) if value is not None else None

    @property
    def is_ready(self) -> bool:
        return self.readiness.get("status") == "READY"

    def _load(self, *, allow_blocked: bool) -> None:
        if not self.root.is_dir():
            raise BookRuntimeError(f"Book root is not a directory: {self.root}")

        self.readiness = self._load_json_required("RUNTIME_READINESS.json")
        if not allow_blocked and self.readiness.get("status") != "READY":
            raise BookRuntimeBlockedError(self.root, self.readiness)

        self.completion = self._load_json_required("STRUCTURED_COMPLETE.json")
        self.metadata = self._load_json_required("book_metadata.json")
        self.qa_policy = self._load_json_required("qa_retrieval_policy.json")
        self._validate_identity()

        toc_name = str(self.metadata.get("toc_file") or "toc_bilingual.json")
        toc_path = self.root / toc_name
        if toc_path.exists():
            self.toc = self._load_json_path(toc_path)
        elif not allow_blocked:
            raise BookRuntimeError(f"Required TOC missing: {toc_path}")

        page_map_name = str(self.metadata.get("page_map_file") or "page_map.csv")
        page_map_path = self.root / page_map_name
        if page_map_path.exists():
            self.page_map = self._read_csv(page_map_path)
        elif not allow_blocked:
            raise BookRuntimeError(f"Required PageMap missing: {page_map_path}")

        self.batches = [self._normalize_batch(path) for path in self._structure_files()]
        self._merge_sections()
        self._merge_objects()
        self._merge_figures()

        search_name = self.completion.get("search_index")
        if search_name:
            candidate = self.root / str(search_name)
            if candidate.exists():
                self.search_index_path = candidate
            elif not allow_blocked:
                raise BookRuntimeError(f"Required final search index missing: {candidate}")

    def _load_json_required(self, name: str) -> dict[str, Any]:
        path = self.root / name
        if not path.exists():
            raise BookRuntimeError(f"Required JSON missing: {path}")
        data = self._load_json_path(path)
        if not isinstance(data, dict):
            raise BookRuntimeError(f"Expected JSON object in {path}")
        return data

    @staticmethod
    def _load_json_path(path: Path) -> Any:
        try:
            with path.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception as exc:  # noqa: BLE001
            raise BookRuntimeError(f"Cannot parse JSON {path}: {exc}") from exc

    @staticmethod
    def _read_csv(path: Path) -> list[dict[str, str]]:
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as fh:
                return list(csv.DictReader(fh))
        except Exception as exc:  # noqa: BLE001
            raise BookRuntimeError(f"Cannot parse CSV {path}: {exc}") from exc

    def _validate_identity(self) -> None:
        canonical = self.metadata.get("book_id")
        identities = {
            "STRUCTURED_COMPLETE": self.completion.get("book_id"),
            "book_metadata": canonical,
            "qa_retrieval_policy": self.qa_policy.get("book_id"),
        }
        bad = {name: value for name, value in identities.items() if value != canonical}
        if bad:
            raise BookRuntimeError(f"Book identity mismatch: canonical={canonical!r}; mismatches={bad}")

        total = self.metadata.get("pdf_total_pages")
        completed = self.completion.get("pdf_pages")
        if total is not None and completed is not None and int(total) != int(completed):
            raise BookRuntimeError(
                f"PDF page-count mismatch: metadata={total}, completion={completed}"
            )

    def _structure_files(self) -> list[Path]:
        files: list[Path] = []
        for path in self.root.rglob("*_structure.json"):
            if not path.is_file():
                continue
            files.append(path)
        return sorted(files, key=lambda p: str(p.relative_to(self.root)))

    @staticmethod
    def _range_pair(value: Any) -> tuple[Any, Any]:
        if isinstance(value, list) and value:
            start = value[0]
            end = value[1] if len(value) > 1 else value[0]
            return start, end
        if isinstance(value, (int, str)):
            return value, value
        return None, None

    @staticmethod
    def _int_or_none(value: Any) -> int | None:
        if value in (None, ""):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _translation_for_structure(self, structure_path: Path, raw: dict[str, Any]) -> Path | None:
        explicit_candidates: list[str] = []

        for key in ("translation_file", "learning_layer_file"):
            value = raw.get(key)
            if isinstance(value, str):
                explicit_candidates.append(value)

        for unit in raw.get("content_units", []) if isinstance(raw.get("content_units"), list) else []:
            if isinstance(unit, dict) and isinstance(unit.get("translation_file"), str):
                explicit_candidates.append(unit["translation_file"])

        for name in explicit_candidates:
            candidate = structure_path.parent / name
            if candidate.exists() and "partial" not in candidate.name.lower():
                return candidate
            candidate = self.root / name
            if candidate.exists() and "partial" not in candidate.name.lower():
                return candidate

        default_name = structure_path.name.replace("_structure.json", "_translation_zh.md")
        default_path = structure_path.with_name(default_name)
        if default_path.exists():
            return default_path

        # Some later batches are at book root while early batches are under chunks/.
        root_candidate = self.root / default_name
        if root_candidate.exists():
            return root_candidate

        return None

    def _normalize_batch(self, path: Path) -> RuntimeBatch:
        raw = self._load_json_path(path)
        if not isinstance(raw, dict):
            raise BookRuntimeError(f"Structure batch must be JSON object: {path}")

        batch_id = str(raw.get("chunk_id") or path.stem.removesuffix("_structure"))
        pdf_start_raw, pdf_end_raw = self._range_pair(raw.get("pdf_pages"))
        printed_start, printed_end = self._range_pair(raw.get("printed_pages"))

        batch = RuntimeBatch(
            id=batch_id,
            source_file=path,
            translation_file=self._translation_for_structure(path, raw),
            pdf_page_start=self._int_or_none(pdf_start_raw),
            pdf_page_end=self._int_or_none(pdf_end_raw),
            printed_page_start=printed_start,
            printed_page_end=printed_end,
            raw=raw,
        )

        if raw.get("chapter_id"):
            batch.chapter_ids.add(str(raw["chapter_id"]))

        for unit in raw.get("content_units", []) if isinstance(raw.get("content_units"), list) else []:
            if not isinstance(unit, dict):
                continue
            if unit.get("chapter_id"):
                batch.chapter_ids.add(str(unit["chapter_id"]))
            self._normalize_frontmatter_unit(batch, unit)

        for section_raw in raw.get("sections", []) if isinstance(raw.get("sections"), list) else []:
            if not isinstance(section_raw, dict) or not section_raw.get("id"):
                continue
            section = self._section_from_raw(batch, section_raw)
            batch.sections.append(section)
            if section.chapter_id:
                batch.chapter_ids.add(section.chapter_id)

        object_sources = (
            ("key_objects", None),
            ("objects", None),
            ("exercises", "exercise"),
            ("problems", "problem"),
        )
        for key, forced_type in object_sources:
            values = raw.get(key, [])
            if not isinstance(values, list):
                continue
            for item in values:
                if isinstance(item, dict):
                    obj = self._object_from_raw(batch, item, forced_type=forced_type)
                    if obj:
                        batch.objects.append(obj)

        figure_values: list[dict[str, Any]] = []
        for key in ("figure_anchors", "figures"):
            values = raw.get(key, [])
            if isinstance(values, list):
                figure_values.extend(v for v in values if isinstance(v, dict))
        for item in figure_values:
            batch.figures.append(self._figure_from_raw(batch, item))

        return batch

    def _normalize_frontmatter_unit(self, batch: RuntimeBatch, unit: dict[str, Any]) -> None:
        unit_type = str(unit.get("type") or "content_unit")
        unit_id = unit.get("unit_id") or unit.get("id")
        if not unit_id:
            return
        if unit_type in {"chapter_opening", "section", "subsection"}:
            pdf_start, pdf_end = self._range_pair(unit.get("pdf_pages") or unit.get("pdf_page"))
            printed_start, printed_end = self._range_pair(unit.get("printed_pages") or unit.get("printed_page"))
            batch.sections.append(
                RuntimeSection(
                    id=str(unit_id),
                    number=str(unit.get("number")) if unit.get("number") is not None else None,
                    title_en=unit.get("title_en"),
                    title_zh=unit.get("title_zh"),
                    chapter_id=str(unit.get("chapter_id")) if unit.get("chapter_id") else None,
                    pdf_page_start=self._int_or_none(pdf_start),
                    pdf_page_end=self._int_or_none(pdf_end),
                    printed_page_start=printed_start,
                    printed_page_end=printed_end,
                    source_batches=[batch.id],
                )
            )
            return

        pdf_start, _ = self._range_pair(unit.get("pdf_pages") or unit.get("pdf_page"))
        printed_start, _ = self._range_pair(unit.get("printed_pages") or unit.get("printed_page"))
        batch.objects.append(
            RuntimeObject(
                id=str(unit_id),
                type=unit_type,
                chapter_id=str(unit.get("chapter_id")) if unit.get("chapter_id") else None,
                name_en=unit.get("title_en"),
                name_zh=unit.get("title_zh"),
                anchor=RuntimeAnchor(
                    pdf_page=self._int_or_none(pdf_start),
                    printed_page=printed_start,
                ),
                source_batch=batch.id,
                raw=unit,
            )
        )

    def _section_from_raw(self, batch: RuntimeBatch, raw: dict[str, Any]) -> RuntimeSection:
        pdf_start, pdf_end = self._range_pair(raw.get("pdf_pages") or raw.get("pdf_page"))
        printed_start, printed_end = self._range_pair(raw.get("printed_pages") or raw.get("printed_page"))
        chapter_id = raw.get("chapter_id") or batch.raw.get("chapter_id")
        return RuntimeSection(
            id=str(raw["id"]),
            number=str(raw.get("number")) if raw.get("number") is not None else None,
            title_en=raw.get("title_en"),
            title_zh=raw.get("title_zh"),
            chapter_id=str(chapter_id) if chapter_id else None,
            pdf_page_start=self._int_or_none(pdf_start),
            pdf_page_end=self._int_or_none(pdf_end),
            printed_page_start=printed_start,
            printed_page_end=printed_end,
            source_batches=[batch.id],
            continued_from=str(raw.get("continued_from")) if raw.get("continued_from") else None,
            continues_in=str(raw.get("continues_in")) if raw.get("continues_in") else None,
        )

    def _object_from_raw(
        self,
        batch: RuntimeBatch,
        raw: dict[str, Any],
        *,
        forced_type: str | None,
    ) -> RuntimeObject | None:
        object_id = raw.get("id") or raw.get("object_id") or raw.get("exercise_id") or raw.get("problem_id")
        if not object_id:
            return None

        anchor_raw = raw.get("anchor") if isinstance(raw.get("anchor"), dict) else {}
        pdf_page = anchor_raw.get("pdf_page") or raw.get("pdf_page")
        printed_page = anchor_raw.get("printed_page") or raw.get("printed_page")
        source_anchor = anchor_raw.get("source_anchor") or raw.get("source_anchor")
        chapter_id = raw.get("chapter_id") or batch.raw.get("chapter_id")
        obj_type = forced_type or str(raw.get("type") or "object")

        return RuntimeObject(
            id=str(object_id),
            type=obj_type,
            chapter_id=str(chapter_id) if chapter_id else None,
            number=str(raw.get("number")) if raw.get("number") is not None else None,
            name_en=raw.get("name_en") or raw.get("title_en"),
            name_zh=raw.get("name_zh") or raw.get("title_zh"),
            formula=raw.get("formula"),
            anchor=RuntimeAnchor(
                pdf_page=self._int_or_none(pdf_page),
                printed_page=printed_page,
                source_anchor=str(source_anchor) if source_anchor else None,
            ),
            source_batch=batch.id,
            raw=raw,
        )

    def _figure_from_raw(self, batch: RuntimeBatch, raw: dict[str, Any]) -> RuntimeFigure:
        figure_id = raw.get("id") or raw.get("figure_id") or raw.get("figure") or raw.get("number")
        if not figure_id:
            figure_id = f"{batch.id}:figure:{len(batch.figures) + 1}"
        anchor_raw = raw.get("anchor") if isinstance(raw.get("anchor"), dict) else {}
        pdf_page = anchor_raw.get("pdf_page") or raw.get("pdf_page")
        printed_page = anchor_raw.get("printed_page") or raw.get("printed_page")
        source_anchor = anchor_raw.get("source_anchor") or raw.get("source_anchor")
        return RuntimeFigure(
            id=str(figure_id),
            title_en=raw.get("title_en"),
            title_zh=raw.get("title_zh"),
            anchor=RuntimeAnchor(
                pdf_page=self._int_or_none(pdf_page),
                printed_page=printed_page,
                source_anchor=str(source_anchor) if source_anchor else None,
            ),
            source_batch=batch.id,
            raw=raw,
        )

    @staticmethod
    def _merge_range_value(old: Any, new: Any, *, choose_min: bool) -> Any:
        if old is None:
            return new
        if new is None:
            return old
        try:
            return min(int(old), int(new)) if choose_min else max(int(old), int(new))
        except (TypeError, ValueError):
            return old

    def _merge_sections(self) -> None:
        for batch in self.batches:
            for incoming in batch.sections:
                existing = self.sections.get(incoming.id)
                if existing is None:
                    self.sections[incoming.id] = incoming
                    continue

                existing.source_batches = sorted(set(existing.source_batches + incoming.source_batches))
                existing.number = existing.number or incoming.number
                existing.title_en = existing.title_en or incoming.title_en
                existing.title_zh = existing.title_zh or incoming.title_zh
                existing.chapter_id = existing.chapter_id or incoming.chapter_id
                existing.pdf_page_start = self._merge_range_value(
                    existing.pdf_page_start, incoming.pdf_page_start, choose_min=True
                )
                existing.pdf_page_end = self._merge_range_value(
                    existing.pdf_page_end, incoming.pdf_page_end, choose_min=False
                )
                existing.printed_page_start = self._merge_range_value(
                    existing.printed_page_start, incoming.printed_page_start, choose_min=True
                )
                existing.printed_page_end = self._merge_range_value(
                    existing.printed_page_end, incoming.printed_page_end, choose_min=False
                )
                existing.continued_from = existing.continued_from or incoming.continued_from
                existing.continues_in = incoming.continues_in or existing.continues_in

    def _section_for_object(self, obj: RuntimeObject) -> str | None:
        if obj.section_id:
            return obj.section_id
        if obj.anchor.pdf_page is None:
            return None

        candidates = [
            section
            for section in self.sections.values()
            if (not obj.chapter_id or not section.chapter_id or section.chapter_id == obj.chapter_id)
            and section.covers_pdf_page(obj.anchor.pdf_page)
        ]
        if not candidates:
            return None

        # Prefer the narrowest page span (usually the most specific subsection).
        def width(section: RuntimeSection) -> int:
            if section.pdf_page_start is None:
                return 10**9
            end = section.pdf_page_end or section.pdf_page_start
            return max(0, end - section.pdf_page_start)

        candidates.sort(key=lambda s: (width(s), -(len(s.number or ""))))
        return candidates[0].id

    @staticmethod
    def _objects_equivalent(left: RuntimeObject, right: RuntimeObject) -> bool:
        return (
            left.type == right.type
            and left.number == right.number
            and left.name_zh == right.name_zh
            and left.name_en == right.name_en
        )

    def _merge_objects(self) -> None:
        for batch in self.batches:
            for incoming in batch.objects:
                incoming.section_id = incoming.section_id or self._section_for_object(incoming)
                existing = self.objects.get(incoming.id)
                if existing is None:
                    self.objects[incoming.id] = incoming
                    continue
                if not self._objects_equivalent(existing, incoming):
                    raise BookRuntimeError(
                        "Conflicting stable object ID "
                        f"{incoming.id!r}: {existing.source_batch} vs {incoming.source_batch}"
                    )
                if existing.anchor.pdf_page is None and incoming.anchor.pdf_page is not None:
                    existing.anchor = incoming.anchor
                existing.section_id = existing.section_id or incoming.section_id
                existing.chapter_id = existing.chapter_id or incoming.chapter_id
                existing.formula = existing.formula or incoming.formula

    def _merge_figures(self) -> None:
        for batch in self.batches:
            for figure in batch.figures:
                existing = self.figures.get(figure.id)
                if existing is None:
                    self.figures[figure.id] = figure
                    continue
                # Repeated figure references are allowed when they point to the same page.
                if (
                    existing.anchor.pdf_page is not None
                    and figure.anchor.pdf_page is not None
                    and existing.anchor.pdf_page != figure.anchor.pdf_page
                ):
                    raise BookRuntimeError(
                        f"Conflicting figure ID {figure.id!r}: "
                        f"PDF {existing.anchor.pdf_page} vs {figure.anchor.pdf_page}"
                    )

    def chapter_ids(self) -> list[str]:
        ids = {section.chapter_id for section in self.sections.values() if section.chapter_id}
        ids.update(obj.chapter_id for obj in self.objects.values() if obj.chapter_id)
        for batch in self.batches:
            ids.update(batch.chapter_ids)
        return sorted(ids)

    def sections_for_chapter(self, chapter_id: str) -> list[RuntimeSection]:
        rows = [section for section in self.sections.values() if section.chapter_id == chapter_id]
        return sorted(rows, key=self._section_sort_key)

    @staticmethod
    def _section_sort_key(section: RuntimeSection) -> tuple[int, str]:
        page = section.pdf_page_start if section.pdf_page_start is not None else 10**9
        return page, section.number or section.id

    def section(self, section_id: str) -> RuntimeSection:
        try:
            return self.sections[section_id]
        except KeyError as exc:
            raise BookRuntimeError(f"Unknown section: {section_id}") from exc

    def object(self, object_id: str) -> RuntimeObject:
        try:
            return self.objects[object_id]
        except KeyError as exc:
            raise BookRuntimeError(f"Unknown object: {object_id}") from exc

    def objects_for_section(self, section_id: str) -> list[RuntimeObject]:
        section = self.section(section_id)
        rows = [obj for obj in self.objects.values() if obj.section_id == section.id]
        return sorted(
            rows,
            key=lambda obj: (
                obj.anchor.pdf_page if obj.anchor.pdf_page is not None else 10**9,
                obj.number or "",
                obj.id,
            ),
        )

    def page_map_row(self, pdf_page: int) -> dict[str, str] | None:
        for row in self.page_map:
            for key in ("pdf_page_index", "pdf_page", "physical_pdf_page"):
                if key not in row:
                    continue
                try:
                    if int(row[key]) == pdf_page:
                        return row
                except (TypeError, ValueError):
                    continue
        return None

    def translation_text(self, batch_id: str) -> str | None:
        for batch in self.batches:
            if batch.id != batch_id:
                continue
            if batch.translation_file and batch.translation_file.exists():
                return batch.translation_file.read_text(encoding="utf-8")
            return None
        raise BookRuntimeError(f"Unknown structure batch: {batch_id}")

    def iter_search_records(self) -> Iterator[dict[str, Any]]:
        if self.search_index_path is None:
            raise BookRuntimeError("Final search index is unavailable")
        with self.search_index_path.open("r", encoding="utf-8") as fh:
            for line_no, line in enumerate(fh, start=1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise BookRuntimeError(
                        f"Invalid search-index JSON at line {line_no}: {exc}"
                    ) from exc
                if isinstance(row, dict):
                    yield row

    def search(self, query: str, *, limit: int = 20) -> list[dict[str, Any]]:
        """Simple deterministic fallback search over the final JSONL index.

        This is intentionally not the eventual semantic ranker.  It gives Phase 1
        a stable, testable retrieval interface while preserving source records and
        anchors exactly as emitted by the final index.
        """

        needle = query.strip().casefold()
        if not needle:
            return []

        ranked: list[tuple[int, int, dict[str, Any]]] = []
        for pos, row in enumerate(self.iter_search_records()):
            exact_fields: list[str] = []
            for key in (
                "id",
                "object_id",
                "number",
                "title_en",
                "title_zh",
                "name_en",
                "name_zh",
            ):
                value = row.get(key)
                if value is not None:
                    exact_fields.append(str(value).casefold())

            blob = json.dumps(row, ensure_ascii=False).casefold()
            if needle not in blob:
                continue

            score = 1
            if needle in exact_fields:
                score = 100
            elif any(field.startswith(needle) for field in exact_fields):
                score = 50
            elif any(needle in field for field in exact_fields):
                score = 20

            ranked.append((-score, pos, row))

        ranked.sort(key=lambda item: (item[0], item[1]))
        return [row for _, _, row in ranked[: max(0, limit)]]

    def summary(self) -> dict[str, Any]:
        return {
            "book_id": self.book_id,
            "structured_version": self.structured_version,
            "runtime_status": self.readiness.get("status"),
            "chapter_count": len(self.chapter_ids()),
            "section_count": len(self.sections),
            "object_count": len(self.objects),
            "figure_count": len(self.figures),
            "batch_count": len(self.batches),
            "page_map_rows": len(self.page_map),
            "has_final_search_index": self.search_index_path is not None,
        }


def load_many(book_roots: Iterable[str | Path], *, allow_blocked: bool = False) -> list[BookRuntime]:
    """Load multiple books for a future CourseRuntime aggregator."""

    return [BookRuntime.open(root, allow_blocked=allow_blocked) for root in book_roots]
