#!/usr/bin/env python3
"""Byte-for-byte archive recovery with mandatory SHA-256 and ZIP CRC checks."""
from __future__ import annotations
import argparse, hashlib, json, os, re, tempfile, zipfile
from pathlib import Path


def safe_name(name: str) -> str:
    if not isinstance(name, str) or not name or name in ('.', '..') or any(c in name for c in '/\\:\x00'):
        raise ValueError('Expected a simple file name, not a path.')
    return name


def digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for data in iter(lambda: source.read(1024*1024), b''):
            digest.update(data)
    return digest.hexdigest()


def verify_file(path: Path, spec: dict) -> None:
    if type(spec.get('bytes')) is not int or spec['bytes'] < 0:
        raise ValueError('Invalid expected byte length.')
    if not re.fullmatch('[0-9a-f]{64}', spec.get('sha256', '')):
        raise ValueError('Invalid SHA-256 format.')
    if not path.is_file() or path.is_symlink() or path.stat().st_size != spec['bytes']:
        raise ValueError('Missing file, unsafe symlink, or wrong length: ' + str(path))
    if digest_file(path) != spec['sha256']:
        raise ValueError('SHA-256 mismatch: ' + str(path))


def merge_parts(root: Path, manifest: dict) -> Path:
    root = root.resolve()
    original = manifest['original']
    target = root / safe_name(original['name'])
    parts = manifest['parts']
    if not isinstance(parts, list) or not parts:
        raise ValueError('No parts specified.')
    names, sources = set(), []
    for number, part in enumerate(parts):
        name = safe_name(part['name'])
        if name in names or not name.endswith(f'.part{number:02d}'):
            raise ValueError('Duplicate or out-of-order part name.')
        names.add(name)
        direct, suffixed = root/name, root/(name+'.bin')
        if direct.exists() and suffixed.exists():
            raise ValueError('Ambiguous duplicate part names: ' + name)
        source = direct if direct.exists() else suffixed
        verify_file(source, part)
        sources.append(source)
    if sum(p['bytes'] for p in parts) != original['bytes']:
        raise ValueError('Part lengths do not sum to the original length.')
    if target.exists():
        verify_file(target, original)
        with zipfile.ZipFile(target) as archive:
            if archive.testzip() is not None:
                raise ValueError('Existing ZIP CRC check failed.')
        return target
    root.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(prefix='merge-', suffix='.partial', dir=root, delete=False)
    temporary = Path(handle.name)
    try:
        with handle as output:
            for source in sources:
                with source.open('rb') as part:
                    for data in iter(lambda: part.read(1024*1024), b''):
                        output.write(data)
            output.flush()
            os.fsync(output.fileno())
        verify_file(temporary, original)
        with zipfile.ZipFile(temporary) as archive:
            if archive.testzip() is not None:
                raise ValueError('Merged ZIP CRC check failed.')
        if target.exists():
            raise FileExistsError('Refusing to overwrite a concurrently created file.')
        temporary.rename(target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--parts-dir', type=Path)
    args = parser.parse_args()
    obj = json.loads(args.manifest.read_text(encoding='utf-8'))
    result = merge_parts(args.parts_dir or args.manifest.resolve().parent, obj)
    print(json.dumps({'ok': True, 'file': str(result), 'sha256': digest_file(result)}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
