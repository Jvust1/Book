#!/usr/bin/env python3
"""Verify a UTF-8 delivery manifest without network access or external tools.
Hashes establish byte identity, NOT the academic correctness of a textbook.
All file names are relative POSIX paths. Font files are deliberately prohibited.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

FONT_EXTENSIONS = {'.ttf', '.otf', '.ttc', '.otc', '.woff', '.woff2', '.pfb', '.pfa'}

def contained_file(root: Path, name: str) -> Path:
    if not isinstance(name, str) or not name or '\\' in name:
        raise ValueError('Use a nonempty relative POSIX file path.')
    p = PurePosixPath(name)
    if p.is_absolute() or PureWindowsPath(name).drive or '..' in p.parts:
        raise ValueError('Absolute paths and parent traversal are prohibited.')
    if p.suffix.lower() in FONT_EXTENSIONS:
        raise ValueError('Font files must not be distributed in this package.')
    path = (root / p).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Resolved file escapes the package root.')
    return path

def verify(root: Path, manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    rows = manifest.get('files')
    if not isinstance(rows, list) or not rows:
        return ['Manifest must contain a nonempty files array.']
    seen: set[str] = set()
    for index, row in enumerate(rows, 1):
        try:
            if not isinstance(row, dict):
                raise ValueError('File entry must be an object.')
            name = row.get('file')
            path = contained_file(root, name)
            if name in seen:
                raise ValueError('Duplicate file entry.')
            seen.add(name)
            expected = row.get('sha256')
            if not isinstance(expected, str) or not re.fullmatch(r'[0-9a-f]{64}', expected):
                raise ValueError('SHA-256 must contain 64 lowercase hexadecimal digits.')
            size = row.get('bytes')
            if type(size) is not int or size < 0:
                raise ValueError('Byte size must be a nonnegative integer.')
            if not path.is_file():
                raise ValueError('File is absent or not a regular file.')
            if path.stat().st_size != size:
                raise ValueError('Byte size mismatch.')
            digest = hashlib.sha256()
            with path.open('rb') as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b''):
                    digest.update(chunk)
            if digest.hexdigest() != expected:
                raise ValueError('SHA-256 mismatch.')
        except (OSError, TypeError, ValueError) as exc:
            errors.append(f'Entry {index}: {exc}')
    return errors

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--manifest', default='manifest.json')
    args = parser.parse_args()
    try:
        path = contained_file(args.root, args.manifest)
        manifest = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(manifest, dict):
            raise ValueError('Manifest root must be an object.')
        errors = verify(args.root, manifest)
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({'ok': False, 'errors': [str(exc)]}, ensure_ascii=False))
        return 2
    print(json.dumps({'ok': not errors, 'files': len(manifest.get('files', [])), 'errors': errors}, ensure_ascii=False))
    return 1 if errors else 0

if __name__ == '__main__':
    raise SystemExit(main())
