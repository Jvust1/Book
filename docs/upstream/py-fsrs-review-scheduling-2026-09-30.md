# Py-FSRS review scheduling integration — 2026-09-30

Upstream: `open-spaced-repetition/py-fsrs`  
Revision inspected: `9446cb06605c597a063aeee49f7d188d42e34dc2`  
License: MIT

## Boundary

Book keeps ownership of:
- textbook/source identity;
- which definitions, theorems, formulas and problems belong to Review;
- user study records and evidence.

FSRS only owns the adaptive **next-review interval**. The adapter accepts a serialized FSRS card plus one of `again/hard/good/easy`, calls upstream `Scheduler.review_card()`, then returns serialized card and review-log dictionaries.

The dependency is lazy and optional. Core Book runtime remains usable without installing `fsrs`.
