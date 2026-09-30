# sentence-transformers semantic retrieval — 2026-09-30

Upstream: `huggingface/sentence-transformers`  
Revision inspected: `4a3b5cd6ec718e421f57e824a41ed3fd99595df6`  
License: Apache-2.0

Book now has an optional semantic retrieval layer for already-structured, source-backed chunks.

- It does not replace keyword search.
- It does not alter textbook facts or learning content.
- The default factory uses `local_files_only=True`, so it will not silently download a model.
- Returned hits preserve Book metadata and source identity.
