# Book 1.3.1 StudyBridge — dated source snapshot

This directory is an isolated archive of the Book-side files for the local Book ↔ mygpt wiring work. It does not replace the active Book application sources.

## Evidence and limits

- Same synthetic Book progress gate/input: baseline **4/13** (exit 1), modified **22/22** (exit 0), rollback **4/13** (exit 1). The rollback copy returned to the baseline SHA-256.
- The prior local wiring suite reported **24/24** tests passing.
- These are local synthetic checks. They do **not** prove a live connection to mygpt, a real model, Codex dot, or Live chat. Model and dot adapters remain unbound; real model calls and real dot calls were zero.
- This PR archives source under `deliverables/`; it is not an application release or a change to Book's active runtime.
- Private local provenance/identity configuration and the generated Spine bundle are intentionally not included in this public source snapshot.

The executable and complete verification package are not attached to this GitHub source archive.