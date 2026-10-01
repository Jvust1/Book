# Evidence-bound source retirement (v10)

`apply_evidence_patch.py` adds the explicit `archive_source_artifact` operation.
It accepts only `running_header`, `decorative_ocr`, or `overlapping_transcription`,
requires an exact original HTML hash, declared source evidence, a nonempty source
comparison, a reason, and live `retained_by` anchors. The full original block is
archived and its anchor alias is recorded. Final checks reject missing retained
anchors and conflicting aliases. No heuristic is allowed to approve retirement.

These checks establish identity and mechanical bounds, NOT semantic equivalence.
An author must visually inspect the original source first. The alias dictionary
is provenance metadata; runtime reader-link migration is NOT implemented here.
Previous patch provenance is retained rather than replaced without history.

```sh
python -m unittest discover -s tools/pdf_delivery -p 'test*.py' -v
python tools/pdf_delivery/apply_evidence_patch.py original_source original_scan.pdf approved_spec.json NEW_output
```

The 26 added synthetic tests cover successful retirement, unchanged source,
full-block archival, alias behavior, rejected unsafe specs and transactional
behavior. The complete local suite has 156 tests. Hosted CI is not claimed.
Do not use this program as a confidentiality-redaction tool. Never overwrite the
original material or infer academic acceptance from successful verification.
