# Book Windows 1.2.0 — paper layout and flexible reflow

Authoritative release checkpoint: `governance/book_windows_1_2_0_20260928.json`.

This release is based on the verified **Book Windows 1.1.0 Go/JavaScript application**, not the earlier FastAPI/React main implementation. The full implementation and all offline content assets are preserved in the hash-locked `Book-1.2.0-Source-and-Tests.zip` in the checkpoint's Drive archive. Recover that source before editing; do not apply an isolated CSS file to the old main UI and call it this release.

## Content and functionality

The default `/document-reader.html` uses the agreed 67 learning-PDF/LaTeX documents and the 186 latest preview/review/practice documents (v3, except contemporary China v4). There are 253 documents and 51,175 content blocks. No new textbook answers are authored by this UI conversion.

Features include A4 automatic pagination, continuous reading, 12–72px text reflow, line/margin/font settings, source vector formulas, original PDF links, local notes/highlights/bookmarks, personal text copies with protected math/images, per-question drafts, self-rating, search, printing and backup/recovery. The old seven-book workspace is retained at `/`.

Source entry points:
- `web/document-reader.html`, `.css`, `.js`
- `web/documents`, `web/document-assets`, `web/document-pdfs`
- `desktop/main.go`, original platform-specific launcher/store
- `tools/build_document_library.py`, `prepare_math_jobs.py`, `render_document_math.cjs`, `finalize_document_library.py`, `classify_practice_sections.py`
- `tests/document_library_test.py`, `document_reader_ui_test.py`, `document_persistence_test.py`, `document_packaged_smoke.py`

## Recover and build

Download the seven ordered source ZIP parts listed in the checkpoint and `PARTS_MANIFEST.json` from Drive. Concatenate in order and verify the source archive SHA-256:

`3a1a755609fda969a687e9123f6b0cce8e0c81c15019f7cd8e12a56c7bac6e7f`

The archive's `SOURCE_MANIFEST.json` checks every included source/asset file. No font binaries, private learning state or executables are in the source archive. `desktop/content.zip` is recreated by the packer.

```sh
python tools/pack_web.py
cd desktop
GOTOOLCHAIN=local GOPROXY=off go test ./...
GOOS=windows GOARCH=amd64 CGO_ENABLED=0 GOTOOLCHAIN=local GOPROXY=off go build -trimpath -ldflags="-s -w -H windowsgui" -o ../Book-1.2.0-Windows-x64.exe .
```

Go1.23.2 and Python3.11+ were used. The Windows user needs only installed Microsoft Edge, not developer runtimes or an API key. Existing `%LOCALAPPDATA%/BookSeven` storage and the old-version mutex are retained. Export a backup and close the old application before upgrading.

## Verified scope

88,178 document/identity assertions, 87 Node tests, 15 Go tests, 95 browser-DOM checks, 13 persistence/protocol checks and 18 final-packaged checks passed. The final Windows x64 GUI PE was cross-compiled. Source ZIP and portable ZIP passed CRC; embedded payload hashes passed the native self-check. The shipped EXE SHA-256 is:

`875ac00edc9d52c3980f77e19a1700e95302945b59c78db71e41aeac01797af6`

Managed Chromium blocked loopback navigation. The explicit test bridge loaded production resources and forwarded requests to the real Go backend; policy was not changed. This is **not** Windows/Edge native launch, direct browser/CSP, native font-import or printer-dialog acceptance. The EXE is unsigned. Reflow is not a claim of identical TeX/browser page breaks or full Word/DOCX compatibility. Existing source/OCR/AI-answer academic boundaries remain.

Drive contains the EXE and source in verified 64MiB parts plus metadata; the complete EXE and portable ZIP are also delivered in the conversation. Large whole-file Drive uploads failed, so they are not falsely recorded as present. Archive-internal `sync: PENDING` records creation before upload; the external GitHub checkpoint records the actual completed part-upload receipts and Drive folder read-back.

No main update or automatic merge was performed.
