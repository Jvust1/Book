#!/usr/bin/env python3
"""Reassemble the verified Book repair download; refuse overwrites (stdlib only)."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys

MANIFEST_SHA256 = '4cefe512f15947318f3f7cb2859fb2f6fa4dff300374f1d98d93e5f03b124ae1'
ARCHIVE_SHA256 = 'c7afb8e26078b635d78c78882cace9284e1cb839f0e4c6f9e5b84264a207c2ee'
ARCHIVE_BYTES = 231547882
ARCHIVE_NAME = 'Book_结构化数据修订包_20260924.zip'


def safe_name(value: object) -> str:
    if not isinstance(value, str) or not value or value in {'.', '..'}:
        raise ValueError('Missing or invalid basename')
    if '/' in value or '\\' in value or ':' in value or Path(value).name != value:
        raise ValueError('Expected a basename, not a path')
    return value


def assemble(manifest_path: Path, parts_dir: Path, output: Path) -> dict:
    raw = manifest_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA256:
        raise ValueError('Unexpected manifest bytes; obtain the exact v3 manifest')
    manifest = json.loads(raw)
    if (manifest['archive_name'], manifest['archive_size_bytes'], manifest['archive_sha256']) != (ARCHIVE_NAME, ARCHIVE_BYTES, ARCHIVE_SHA256):
        raise ValueError('Archive identity differs from the fixed repair release')
    parts = manifest['parts']
    if len(parts) != 8 or [p['order'] for p in parts] != list(range(1, 9)):
        raise ValueError('Expected the eight ordered v3 parts')
    names = [safe_name(p['name']) for p in parts]
    if len(set(names)) != len(names):
        raise ValueError('Duplicate part names')
    root = parts_dir.resolve(strict=True)
    sources = []
    for part, name in zip(parts, names):
        if not isinstance(part['size_bytes'], int) or not 0 < part['size_bytes'] <= ARCHIVE_BYTES:
            raise ValueError('Invalid part length')
        if not re.fullmatch('[a-f0-9]{64}', part['sha256']):
            raise ValueError('Invalid part digest')
        candidates = [root / name, root / (name + '.bin')]
        available = [p for p in candidates if p.is_file() and not p.is_symlink()]
        if len(available) != 1:
            raise ValueError('Missing or ambiguous part: ' + name)
        path = available[0]
        if path.resolve().parent != root or path.stat().st_size != part['size_bytes']:
            raise ValueError('Unexpected part path or size: ' + name)
        sources.append(path)
    if sum(p['size_bytes'] for p in parts) != ARCHIVE_BYTES:
        raise ValueError('Part lengths do not sum to the full archive')
    # A failed verification never overwrites an existing archive. The partial file
    # created by this invocation is removed on failure; original inputs stay intact.
    total = 0
    digest = hashlib.sha256()
    created = False
    try:
        with output.open('xb') as target:
            created = True
            for spec, source in zip(parts, sources):
                part_digest = hashlib.sha256()
                count = 0
                with source.open('rb') as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b''):
                        count += len(block)
                        if count > spec['size_bytes']:
                            raise ValueError('Part grew while reading')
                        part_digest.update(block)
                        digest.update(block)
                        target.write(block)
                if count != spec['size_bytes'] or part_digest.hexdigest() != spec['sha256']:
                    raise ValueError('Part hash mismatch: ' + spec['name'])
                total += count
            if total != ARCHIVE_BYTES or digest.hexdigest() != ARCHIVE_SHA256:
                raise ValueError('Reassembled archive identity mismatch')
            target.flush()
            os.fsync(target.fileno())
    except BaseException:
        if created:
            output.unlink(missing_ok=True)
        raise
    return {'status': 'PASS', 'archive': str(output), 'size_bytes': total,
            'sha256': digest.hexdigest(), 'parts_verified': len(parts)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--parts-dir', type=Path, default=Path('.'))
    parser.add_argument('--output', type=Path, default=Path(ARCHIVE_NAME))
    args = parser.parse_args()
    try:
        result = assemble(args.manifest, args.parts_dir, args.output)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'status': 'FAIL', 'error': str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
