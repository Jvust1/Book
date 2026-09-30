# MinerU external ingestion — 2026-09-30

Upstream: `opendatalab/MinerU`  
Revision: `ed50cc15bc2c9bfb00520dadfe61979866e62236`

MinerU is Apache-2.0 with additional commercial-threshold terms in its repository license. Book therefore treats MinerU strictly as an **external optional CLI tool** and does not vendor MinerU source code.

The adapter uses the documented 4.0 command shape:
`mineru-kit parse document.pdf -o document.md --tier standard`.

Parsed Markdown is still non-authoritative until it passes Book's source/provenance pipeline.
