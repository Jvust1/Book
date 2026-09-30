# MarkItDown ingestion fallback — 2026-09-30

Upstream: `microsoft/markitdown`  
Revision: `b8f79c57ebc0044be41323d89b2a45d3fda8460e`  
License: MIT

Book already has high-fidelity Docling ingestion. MarkItDown is added as a lightweight explicit local-file fallback. The generic `DocumentIngestFallback` tries configured ingestors in order and preserves the first successful backend. Neither backend can mutate canonical textbook structures automatically.
