#!/usr/bin/env python3
"""Restore Book Windows 1.0.0 into a NEW directory from verified rc4 + cumulative delta.
No network, no code execution from archives, no mutation of original artifacts.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

BASELINE_SHA = 'd27f90f62d89f17778d6dfc628a70ff3963a4e33782e4d517d2e97cfa314b91e'

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def safe_path(name: str) -> str:
    p = PurePosixPath(name)
    if not name or '\\' in name or p.is_absolute() or any(x in ('', '.', '..') for x in name.split('/')) or ':' in name or p.as_posix() != name:
        raise ValueError('Unsafe archive path: ' + repr(name))
    return name

def checked_entries(z: zipfile.ZipFile) -> dict[str, zipfile.ZipInfo]:
    result: dict[str, zipfile.ZipInfo] = {}
    total = 0
    for info in z.infolist():
        if info.is_dir():
            safe_path(info.filename.rstrip('/'))
            continue
        key = safe_path(info.filename)
        if key in result or stat.S_ISLNK(info.external_attr >> 16):
            raise ValueError('Duplicate path or symbolic link in archive')
        total += info.file_size
        if total > 2 * 1024**3:
            raise ValueError('Archive exceeds expected 2 GiB source limit')
        result[key] = info
    return result

def restore(baseline: Path, delta: Path, destination: Path, expected_delta_sha: str) -> dict:
    baseline, delta, destination = baseline.resolve(), delta.resolve(), destination.absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError('Destination must be a NEW, non-existing directory')
    if len(expected_delta_sha) != 64 or any(c not in '0123456789abcdefABCDEF' for c in expected_delta_sha):
        raise ValueError('Provide the trusted SHA-256 from the release manifest')
    if digest(baseline) != BASELINE_SHA or digest(delta) != expected_delta_sha.lower():
        raise ValueError('Source or delta SHA-256 mismatch; nothing restored')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(baseline) as old, zipfile.ZipFile(delta) as new:
        old_entries, new_entries = checked_entries(old), checked_entries(new)
        manifest = json.loads(new.read('delta-manifest.json'))
        if manifest.get('schema') != 'book-teaching-delta-v1' or manifest.get('baseline_sha256') != BASELINE_SHA:
            raise ValueError('Wrong delta manifest or baseline')
        target = manifest['result_files']
        expected = {safe_path(f['path']): f for f in target}
        if len(expected) != len(target):
            raise ValueError('Duplicate target manifest entries')
        roots = {PurePosixPath(x).parts[0] for x in old_entries}
        if roots != {'Book-Seven-Windows'}:
            raise ValueError('Unexpected baseline directory layout')
        old_map = {x.split('/', 1)[1]: x for x in old_entries if '/' in x}
        with tempfile.TemporaryDirectory(prefix='book-restore-', dir=destination.parent) as temp:
            stage = Path(temp) / 'source'
            stage.mkdir()
            for path, entry in expected.items():
                payload = 'payload/' + path
                if payload in new_entries:
                    stream = new.open(new_entries[payload])
                elif path in old_map:
                    stream = old.open(old_entries[old_map[path]])
                else:
                    raise ValueError('Missing source bytes: ' + path)
                dest = stage / path
                dest.parent.mkdir(parents=True, exist_ok=True)
                with stream, dest.open('wb') as out:
                    shutil.copyfileobj(stream, out)
                if dest.stat().st_size != entry['bytes'] or digest(dest) != entry['sha256']:
                    raise ValueError('Restored file mismatch: ' + path)
            if destination.exists() or destination.is_symlink():
                raise ValueError('Destination appeared during restore; refusing overwrite')
            stage.rename(destination)
    return {'build': manifest['build'], 'verified_files': len(expected), 'output': str(destination), 'baseline_unchanged': True, 'network_requests': 0}

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--delta', type=Path, required=True)
    parser.add_argument('--sha256', required=True, help='Trusted delta SHA-256, not a value guessed from filenames')
    parser.add_argument('--output', type=Path, required=True, help='A new directory; never an existing application/data folder')
    args = parser.parse_args()
    try:
        result = restore(args.baseline, args.delta, args.output, args.sha256)
    except (ValueError, OSError, KeyError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        parser.exit(2, f'Restore failed: {exc}\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
