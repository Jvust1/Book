#!/usr/bin/env python3
"""Normalize known cross-batch stable-object identity drift in Functional Analysis.

The structured book intentionally repeats a small number of stable object IDs
across chunk boundaries when one mathematical object continues or is enriched in
a later chunk.  Runtime loading keeps a strict identity guard, so those repeated
rows must agree on identity fields (type, number, canonical English/Chinese
name).  This migration fixes only the three identity-label drifts established by
repository diagnostics; it does not infer or rewrite arbitrary objects.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


CANONICAL_IDENTITY_FIELDS: dict[str, dict[str, str]] = {
    "ex_ch2_7_10": {
        "name_zh": "Poisson 核卷积在 L^p 中的压缩性与近似恒等性",
    },
    "def_ch5_infinite_bernoulli_space": {
        "name_en": "infinite Bernoulli space X=Z_2^∞",
    },
    "thm_ch6_4_2_holder_nowhere_diff": {
        "name_zh": "Brownian 路径的 Hölder 正则性与粗糙性",
    },
}

OBJECT_LIST_KEYS = ("key_objects", "objects", "exercises", "problems")


def _object_id(row: dict[str, Any]) -> str | None:
    value = row.get("id") or row.get("object_id") or row.get("exercise_id") or row.get("problem_id")
    return str(value) if value else None


def _structure_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*_structure.json") if path.is_file())


def normalize_known_identities(root: Path, *, write: bool = False) -> dict[str, Any]:
    changes: list[dict[str, Any]] = []
    occurrences: dict[str, list[dict[str, Any]]] = {object_id: [] for object_id in CANONICAL_IDENTITY_FIELDS}

    for path in _structure_files(root):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            continue
        changed_file = False

        for key in OBJECT_LIST_KEYS:
            values = data.get(key)
            if not isinstance(values, list):
                continue
            for row in values:
                if not isinstance(row, dict):
                    continue
                object_id = _object_id(row)
                if object_id not in CANONICAL_IDENTITY_FIELDS:
                    continue

                canonical = CANONICAL_IDENTITY_FIELDS[object_id]
                for field, target in canonical.items():
                    old = row.get(field)
                    if old != target:
                        row[field] = target
                        changed_file = True
                        changes.append(
                            {
                                "file": str(path.relative_to(root)),
                                "source_key": key,
                                "id": object_id,
                                "field": field,
                                "old": old,
                                "new": target,
                            }
                        )

                occurrences[object_id].append(
                    {
                        "file": str(path.relative_to(root)),
                        "source_key": key,
                        "type": row.get("type") or ("exercise" if key == "exercises" else "problem" if key == "problems" else None),
                        "number": str(row.get("number")) if row.get("number") is not None else None,
                        "name_en": row.get("name_en") or row.get("title_en"),
                        "name_zh": row.get("name_zh") or row.get("title_zh"),
                    }
                )

        if changed_file and write:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    consistency: dict[str, dict[str, Any]] = {}
    all_consistent = True
    for object_id, rows in occurrences.items():
        canonical = CANONICAL_IDENTITY_FIELDS[object_id]
        found = bool(rows)
        fields_consistent = True
        for row in rows:
            for field, target in canonical.items():
                if row.get(field) != target:
                    fields_consistent = False
        consistency[object_id] = {
            "occurrence_count": len(rows),
            "canonical_fields": canonical,
            "consistent": fields_consistent,
        }
        if found and not fields_consistent:
            all_consistent = False

    return {
        "status": "PASS" if all_consistent else "FAIL",
        "write": write,
        "known_identity_count": len(CANONICAL_IDENTITY_FIELDS),
        "changed_occurrences": len(changes),
        "changes": changes,
        "identity_consistency": consistency,
        "all_known_identities_consistent": all_consistent,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("book_root", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    report = normalize_known_identities(args.book_root, write=args.write)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["all_known_identities_consistent"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
