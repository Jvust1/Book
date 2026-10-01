# Book PDF delivery tools

These tools audit or preserve supplied source material. They do not certify academic correctness, approve historical facts as current, or perform confidentiality redaction.

- `audit_v5_glyphs.py`: non-whitespace extracted-character/position counters, with explicit 0.05pt rounding tolerance. Page-count changes reject positional pairing. PDF glyph extraction is not a complete drawing-operation or semantic comparison.
- `restore_missing_glyphs.py`: exact-hash-gated restoration of explicit source glyphs, refusing input overwrites, duplicates and unapproved changes. Clipped forms may retain non-visible page resources; NEVER use it to remove secrets. The optional Identity-H CID route isolates an approved glyph from overlapping editorial marks and verifies its Unicode, coordinates and bounding box before copying it.
- `reflow_preserved_html.py`: allowlisted HTML, original block text instead of reader cleanup, no external asset requests, source provenance labels retained, actual A4 and declared text sizes. Existing OCR errors and incomplete source image crops are not fixed by reflow.
- `build_preserved_collection.py`: build all selected local source documents and optionally combine each mode/size with chapter bookmarks. Output directories must be new.

Install the pinned Python requirements and the necessary WeasyPrint system libraries. Noto Serif CJK SC and Noto Sans CJK SC must be present. No fonts are distributed. This is NOT a true-Shusong or Windows-reader acceptance claim.

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s . -p 'test*.py' -v
python build_preserved_collection.py /path/to/source /path/to/new-output --sizes 10 12 15 --jobs 2 --combine
```

The private artifact package holds actual textbook source JSON, image assets, approved repair specs and source-level evidence. Public code/tests use only generic and synthetic material. Full-source citations and AI-reference-answer labels are preserved, not silently promoted into publisher answers.
