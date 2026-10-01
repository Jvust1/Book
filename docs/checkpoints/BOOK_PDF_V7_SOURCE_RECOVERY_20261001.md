# Book PDF v7 — section 4.6 and six-book source recovery

Date: 2026-10-01. **FULL_RELEASE_NOT_READY** remains in force. This batch does not re-do lecture 5, merge main, overwrite canonical textbook data, or claim Windows/true-Shusong acceptance.

## New section delivery

Financial Economics Ten Lectures section 4.6: original scan PDF 102–108, printed 83–89; begins at 4.6 and ends before 4.7. Reconstructed and visually checked against the seven original page images. Includes proposition 4.1, theorem 4.4 and its five-part equivalence proof, and eight numbered equations 4.24–4.31. Four explicit source-printing doubts retained as notes, not silently corrected.

This addresses the proof chain corresponding to old 15px full-book pages 138–140 as a standalone source-reflow candidate. The 334-page old book is NOT claimed fully reflowed or replaced.

- 10px = 7.5pt, 4 A4 pages, 158869 bytes, SHA-256 1866a25b64a1277928b49b006f360f5e4501b4302064bb81cf82b6313fa2cede.
- 12px = 9pt, 5 A4 pages, 159673 bytes, SHA-256 abcb033367d78d0c179d4a75ed44bdcde04609f1bc5a8373bfa264b06553707e.
- 15px = 11.25pt, 6 A4 pages, 161910 bytes, SHA-256 22ed232b00b0ffda99ec3ad479cd96bab630520a4da8101f8d2cb53dd66fbc02.
- Shared body SHA-256: 435ff4653a17f86f9be2cd012a583daf7215e8a4ce1d8553e3b219b8d8a29a7a.
- Noto Serif CJK SC substitute and Latin Modern Math; NOT Shusong. No font files distributed.

Two XeLaTeX passes per size. Final Overfull, missing character, undefined command, LaTeX error and font-warning counts all zero. All 15 pages rendered and contact sheets inspected. Three additional Poppler key pages inspected. No out-of-page text, empty page, NUL or U+FFFD. Body CJK count 4243 in each size; whitespace-stripped character multisets identical without a math-symbol normalization exception. Same-environment rebuild in a different path containing spaces is byte-identical for 3/3 PDFs. Not an independent academic audit.

## Recovered source baseline and candidate mapping

Recovered existing nine-part 1.3.0-final-r2 archive: 569426102 bytes; SHA-256 9c881dd2548fdf0a72b5811e65f032ae56b25c5e68c6092e82962fbaef56c22f. All nine part hashes, ZIP CRC and 30723 original payload hashes (1110207094 uncompressed bytes) verified. The extra ZIP entry is the manifest itself.

253 reading JSON documents contain HTML blocks: fa21, pde29, fe41, pf60, ce45, mf57. By mode: learn67, preview62, review62, practice62. NOT the later Windows1.3.1 249-document baseline.

12 freshly fetched v5 manifests yield 253 unique book/chapter/mode candidates, all with the same page counts. All 253 historic source PDFs independently match their recorded lengths, hashes and actual page counts. For 186 teaching-mode documents the v4 full-source hash equals the v5 manifest derived_from hash. No analogous lineage field exists for 67 learning documents.

**All 253 historic PDF hashes differ from v5 manifest hashes. Content equivalence is NOT established.** The registry records candidate/lineage levels, not final editable-source approval. Original quality labels and reader cleanup are preserved, not globally promoted.

29031 distinct img-src assets exist, none missing or external: 28838 SVG,190 PNG,3 JPG. 17292 blocks reference images;4142 explicitly have editable=false. SVG paths are not semantic LaTeX.

## Artifacts and integrity

Private folder: https://drive.google.com/drive/folders/1eOBXRPCqxqbKIP7RrRPEj7KisTajlrbG

Small delivery ZIP (three PDFs, LaTeX, QA,253-row registry,tools): https://drive.google.com/file/d/1F544QwbEQdsanvDvbVRZYnsGcM8hnh5d/view
3637408 bytes; SHA-256 2284132d6e552564b8fa7c5ae1f953d1c00e667ef3ce98e7027786c90ed654ea. Raw Drive download roundtrip, ZIP CRC and all69 payload hashes passed.

Chinese report: https://drive.google.com/file/d/1So7ARm28R31650W6ynjtiNg-muiU0Gnw/view
253-row candidate table: https://drive.google.com/file/d/1CMQh5iE-6L9wjyx58q0AaO6E3WL6v5sC/view

Historical source/asset ZIP:181688857 bytes; SHA-256 ddb856eb590fd09eb71dcd7e44e43987b0ceb9facc468d09112e1049ca694c16.29284 original payload hashes and CRC pass. Full upload failed before invocation with UNREGISTERED_FILE_REFERENCE; original ZIP preserved, uploaded as five raw40MiB parts instead. No lossy processing. All five writes succeeded. No separate full remote five-part roundtrip is claimed by this checkpoint.
Parts manifest: https://drive.google.com/file/d/1e38UJT9DUh89GtiHYXIH6CgvyZnS5ikP/view
Colab merge Notebook: https://drive.google.com/file/d/1yMmyGCy3YfwxJMfJaA6Cv0ut7v44ZsrN/view
Actual local five-part merge reproduces full SHA/CRC. Notebook6 code cells pass syntax checks; user-account Colab auth/download/upload not executed here.

## Code and tests

Generic registry builder and raw-byte merger plus synthetic tests added under tools/pdf_delivery.27 new tests plus16 existing verifier tests rerun:43 local tests pass. No private textbook text, source illustrations, fonts or PDFs are added to public GitHub. Hosted CI status is NOT_CLAIMED; no manual workflow dispatch.

```sh
python -m unittest discover -s tools/pdf_delivery -p 'test*.py' -v
python tools/pdf_delivery/build_source_registry.py /path/to/original.zip /path/to/v5_manifests registry.json
python tools/pdf_delivery/merge_raw_parts.py /path/to/parts_manifest.json
```

Next: use recovered253 documents/resources and explicit v5 candidates for per-document content differences and same-source all-mode reflow. Do not repeat source discovery or lecture5/section4.6 generation. Remaining: full v5 content equivalence, other sections/books/modes/sizes, true Shusong, target Windows-reader/printing acceptance, full release sampling and independent doubt review.
