"""Original, file-backed chapter fixture. No existing textbook material is copied."""
import json
from pathlib import Path

from tests.runtime_fixture_factory import dump_json, main_book_entry, make_repo, write_course, write_ready_book

COURSE_ID = "original_algebra_pilot"
BOOK_ID = "original_algebra_book"
SECTION_ID = "original_s01"
SOURCE_ID = "doubling_rule"
QUESTION = "倍增规则"
EXPECTED = "4"


def write_synthetic_chapter(root: Path) -> Path:
    repo = make_repo(root)
    objects = [
        {"type": "definition", "id": SOURCE_ID, "number": "1.1", "name_zh": QUESTION,
         "name_en": "Doubling rule", "formula": "d(x)=x+x=2x",
         "content_zh": "原创试点：把一个数与自身相加得到它的两倍。对于 $$x=2$$，有 $$x+x=4$$。",
         "anchor": {"pdf_page": 2, "printed_page": 1, "source_anchor": "original:pdf:2:doubling_rule"}},
        {"type": "exercise", "id": "doubling_exercise", "number": "1.2", "name_zh": "倍增练习",
         "content_zh": "原创练习：计算 2+2。先独立作答，再使用本地演算区核对。",
         "anchor": {"pdf_page": 2, "printed_page": 1, "source_anchor": "original:pdf:2:doubling_exercise"}},
    ]
    records = [{"book_id": BOOK_ID, **{k: v for k, v in row.items() if k != "anchor"}, **row["anchor"]}
               for row in objects]
    book = repo / "books" / "original-algebra"
    write_ready_book(book, book_id=BOOK_ID, objects=objects, search_records=records,
                     sections=[{"id": SECTION_ID, "number": "1.1", "title_zh": "原创倍增小节",
                                "title_en": "Original doubling section", "pdf_pages": [2, 2], "printed_pages": [1, 1]}])
    metadata = json.loads((book / "book_metadata.json").read_text(encoding="utf-8"))
    metadata.update(title_zh="原创代数试点", title_en="Original algebra pilot")
    dump_json(book / "book_metadata.json", metadata)
    complete = json.loads((book / "STRUCTURED_COMPLETE.json").read_text(encoding="utf-8"))
    complete["printed_final_page"] = 1
    dump_json(book / "STRUCTURED_COMPLETE.json", complete)
    (book / "page_map.csv").write_text("pdf_page,printed_page,page_label\n1,,Cover\n2,1,1\n", encoding="utf-8")
    # Original user-selectable PDF is generated independently by the browser test.
    # These structured files are temporary runtime inputs, not canonical content.
    write_course(repo / "courses" / "original-algebra", course_id=COURSE_ID, main_book_id=BOOK_ID,
                 book_entries=[main_book_entry(BOOK_ID, "../../books/original-algebra")])
    dump_json(repo / "library" / "library.json", {
        "schema_version": "library_manifest_v1", "library_id": "original_pilot_library", "name": "原创试点书架",
        "courses": [{"course_id": COURSE_ID, "name": "原创代数试点", "path": "../courses/original-algebra",
                     "enabled": True, "order": 1}],
    })
    return repo
