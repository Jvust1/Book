#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from runtime.document_ingest import create_document_ingest_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert a local source document into Book staging markdown.")
    parser.add_argument("source")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    result = create_document_ingest_pipeline().convert_local(args.source)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result.markdown, encoding="utf-8")
    manifest = output.with_suffix(output.suffix + ".manifest.json")
    manifest.write_text(
        json.dumps(result.manifest(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"output": str(output), "manifest": str(manifest), **result.manifest()}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
