from __future__ import annotations

import json
from pathlib import Path


def dump_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def make_repo(root: Path) -> Path:
    repo = root.resolve()
    (repo / "runtime").mkdir(parents=True, exist_ok=True)
    (repo / "books").mkdir(parents=True, exist_ok=True)
    (repo / "courses").mkdir(parents=True, exist_ok=True)
    return repo


def write_ready_book(
    root: Path,
    *,
    book_id: str,
    readiness: str = "READY",
    objects: list[dict[str, object]] | None = None,
    figures: list[dict[str, object]] | None = None,
) -> None:
    root.mkdir(parents=True, exist_ok=True)
    dump_json(
        root / "RUNTIME_READINESS.json",
        {
            "status": readiness,
            "book_id": book_id,
            "structured_version": "v1",
            "missing_required_files": [],
            "stale_files": [] if readiness == "READY" else ["search_index_v1.jsonl"],
        },
    )
    dump_json(
        root / "STRUCTURED_COMPLETE.json",
        {
            "status": "STRUCTURED_COMPLETE",
            "book_id": book_id,
            "pdf_pages": 2,
            "printed_final_page": 2,
            "version": "v1",
            "audit_fail_count": 0,
            "search_index": "search_index_v1.jsonl",
        },
    )
    dump_json(
        root / "book_metadata.json",
        {
            "book_id": book_id,
            "title_en": "Fixture",
            "title_zh": "测试教材",
            "pdf_total_pages": 2,
            "toc_file": "toc_bilingual.json",
            "page_map_file": "page_map.csv",
        },
    )
    dump_json(root / "qa_retrieval_policy.json", {"version": "1", "book_id": book_id})
    dump_json(
        root / "toc_bilingual.json",
        {
            "chapters": [
                {
                    "id": "chapter_01",
                    "number": "1",
                    "title_en": "Test chapter",
                    "title_zh": "测试章",
                    "sections": [
                        {
                            "id": "ch01_s01",
                            "number": "1",
                            "title_en": "Section",
                            "title_zh": "小节",
                        }
                    ],
                }
            ]
        },
    )
    dump_json(
        root / "chunk_001a_structure.json",
        {
            "chunk_id": "chunk_001a",
            "pdf_pages": [1, 2],
            "printed_pages": [1, 2],
            "chapter_id": "chapter_01",
            "sections": [
                {
                    "id": "ch01_s01",
                    "number": "1",
                    "title_en": "Section",
                    "title_zh": "小节",
                    "pdf_pages": [1, 2],
                    "printed_pages": [1, 2],
                }
            ],
            "key_objects": objects or [],
            "figure_anchors": figures or [],
        },
    )
    (root / "chunk_001a_translation_zh.md").write_text("# 测试学习层\n", encoding="utf-8")
    (root / "page_map.csv").write_text(
        "pdf_page,printed_page,page_label\n1,1,1\n2,2,2\n",
        encoding="utf-8",
    )
    (root / "search_index_v1.jsonl").write_text(
        json.dumps(
            {"id": "section_ch01_s01", "book_id": book_id, "type": "section"},
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def write_course(
    course_dir: Path,
    *,
    course_id: str,
    book_entries: list[dict[str, object]],
    main_book_id: str,
) -> None:
    dump_json(
        course_dir / "course.json",
        {
            "schema_version": "course_manifest_v1",
            "course_id": course_id,
            "name": course_id,
            "language": "bilingual",
            "status": "active",
            "main_book_id": main_book_id,
            "books": book_entries,
        },
    )


def main_book_entry(book_id: str, path: str) -> dict[str, object]:
    return {
        "book_id": book_id,
        "role": "main",
        "path": path,
        "required": True,
        "enabled": True,
    }
