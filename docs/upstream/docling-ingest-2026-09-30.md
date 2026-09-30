# Docling ingestion — 2026-09-30

Upstream: `docling-project/docling`  
Revision: `d6f03078ad364108df3e7e82e8f0dcc3fd7f39ea`  
License: MIT

Book uses Docling only for explicit local source conversion to Markdown. The adapter does not silently download or ingest files and does not mutate canonical textbook structures. Converted Markdown remains an input that must still pass Book's source/provenance pipeline before becoming authoritative learning content.
