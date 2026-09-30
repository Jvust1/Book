# RapidFuzz fuzzy retrieval — 2026-09-30

Upstream: `rapidfuzz/RapidFuzz`  
Revision inspected: `db6e504539a9c895180b266a06b36a32cb6029ee`  
License: MIT

Book now uses exact retrieval first. If exact search returns no rows, a fuzzy object-title fallback compares only stable object ID, number, Chinese title and English title. Every hit still passes through `source_identity_for(course, "object", object_id)`, so typo tolerance cannot bypass canonical textbook provenance.

RapidFuzz is optional; Python's deterministic SequenceMatcher remains the fallback.
