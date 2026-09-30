# FAISS semantic index — 2026-09-30

Upstream: `facebookresearch/faiss`  
Revision inspected: `88a28bcd80aa4469bd15520c510186c98f51d985`  
License: MIT

Book's sentence-transformers integration already owns semantic embeddings. This addition only accelerates nearest-neighbor ranking for larger approved textbook chunk sets.

- Source IDs and metadata stay Book-owned.
- FAISS receives only embedding matrices.
- The default factory remains local-first and does not download a model unless the caller explicitly allows it.
- Small corpora can keep using the existing in-memory cosine index.
