# Docling-first source ingestion — 2026-10-01

Upstream: `docling-project/docling`  
Revision inspected: `d6f03078ad364108df3e7e82e8f0dcc3fd7f39ea`  
License: MIT

Book now has one explicit local source-ingest pipeline: Docling first for high-fidelity document structure, MarkItDown as fallback. Output is staging Markdown plus a SHA-256 manifest. The pipeline never mutates canonical textbook JSON, source identities, page maps, or learning content automatically.
