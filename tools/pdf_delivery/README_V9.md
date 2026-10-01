# Evidence-bound source patches and table reflow (v9)

The generic patcher applies an explicitly reviewed JSON specification to the supported `book-reflow-document-v1` source schema. The specification must identify the complete source scan, original JSON and replaced HTML by SHA-256. It does not infer corrections, perform OCR, access the network, or certify source accuracy.

Supported operations: `replace`, `insert_after`, `move_after`, and `retire_duplicate`. Retired duplicate blocks are archived in the output JSON; their nonempty text must still occur in the retained block after whitespace-only normalization. Unaffected original blocks must remain exactly equal. Inputs are preserved, stale reader fields are cleared only where needed, and full academic acceptance remains false. Use a new destination outside the original source root. Prepare specifications only after inspecting the matching original page images.

```sh
python -m pip install -r tools/pdf_delivery/requirements.txt
python -m unittest discover -s tools/pdf_delivery -p 'test*.py' -v
python tools/pdf_delivery/apply_evidence_patch.py SOURCE_ROOT SOURCE_SCAN.pdf APPROVED_SPEC.json NEW_PATCH_DIRECTORY
python tools/pdf_delivery/reflow_preserved_html.py NEW_PATCH_DIRECTORY/source/documents/example.json NEW_PATCH_DIRECTORY/source NEW_OUTPUT.pdf --px 15 --edition v9 --evidence-tables --evidence-notice "Only the explicitly reviewed corrections have been applied."
```

`--edition`, `--evidence-tables`, and `--evidence-notice` are optional. The default v8r2 rendering profile is unchanged. The evidence-table profile uses the declared prose size, preserves table structure, and keeps direct table-cell span groups together without scaling the whole page. Use explicit nonbreaking numeric groups in reviewed table HTML; visual checking is still required.

The full suite passed 130 local tests in the v9 delivery environment, including 45 new synthetic patch/profile tests. No hosted CI result is claimed. Local tests, multiset preservation, pixel equality and file hashes do not establish academic correctness or Windows-reader acceptance. Cross-path v9 rebuilds had identical text/pixels but different raw PDF bytes.

Private scan extracts, correction specifications, textbook JSON/HTML, figures and output PDFs are in the private Drive delivery; none are included here. Noto is a substitute, not Shusong. Font files are not distributed.
