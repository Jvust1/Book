"""Deterministic, allowlisted original-reader source delivery; no canonical books.

build reads immutable Git blobs; verify/extract/repack do not require a Git checkout.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import re
import subprocess
import tarfile
import zlib
from pathlib import Path, PurePosixPath

ROOT = "book-reader-pilot"
MANIFEST = "pilot-source-manifest.json"
README_SOURCE = "docs/upstream/reader-pilot-package-README.md"
MAX_FILES = 4096
MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_TOTAL_BYTES = 64 * 1024 * 1024
MAX_ARCHIVE_BYTES = 32 * 1024 * 1024
MAX_TAR_BYTES = MAX_TOTAL_BYTES + MAX_FILE_BYTES + MAX_FILES * 1024 + 10240
EXACT = frozenset({
    "app/__init__.py", "app/api/requirements.txt", "app_tests/__init__.py",
    "app_tests/synthetic_chapter.py", "app_tests/synthetic_pilot_server.py", "app_tests/test_synthetic_chapter.py",
    "tests/runtime_fixture_factory.py", "tests/test_symbolic_answer.py", "tests/test_symbolic_safety.py",
    "tests/test_reader_pilot_source.py", "README.md",
    "requirements-extras/symbolic.txt", "requirements-extras/pilot-api.txt",
    "tools/check_symbolic_answer.py", "tools/build_reader_pilot_source.py",
    "app/web/e2e/syntheticPdf.ts", "app/web/scripts/prepare-pdf-assets.mjs", "app/web/index.html",
    "app/web/package.json", "app/web/package-lock.json", "app/web/vite.config.ts",
    "app/web/playwright.config.ts", "app/web/playwright.pilot.config.ts",
    "app/web/tsconfig.json", "app/web/tsconfig.app.json", "app/web/tsconfig.node.json",
    "docs/upstream/reader-pilot-package-README.md", "docs/upstream/licenses/SymPy-1.14.0-LICENSE.txt",
    "docs/upstream/katex-reader-2026-09-30.md", "docs/upstream/pdfjs-local-source-2026-09-30.md",
    "docs/upstream/react-markdown-qa-2026-09-30.md", "docs/upstream/mathjs-practice-2026-09-30.md",
    "docs/upstream/fuse-local-pdf-search-2026-09-30.md", "docs/upstream/zod-source-contracts-2026-09-30.md",
    "docs/upstream/tanstack-reader-cache-2026-09-30.md", "docs/upstream/safe-sympy-input-2026-09-30.md",
    "docs/upstream/combined-reader-pilot-2026-09-30.md", "docs/upstream/zod-learning-response-contracts-2026-09-30.md",
    "docs/upstream/session-view-storage-recovery-2026-09-30.md",
})
REQUIRED = frozenset({"app/api/main.py", "app/web/package-lock.json", "app_tests/synthetic_chapter.py",
                      "runtime/symbolic_answer.py", "requirements-extras/pilot-api.txt",
                      "docs/upstream/reader-pilot-package-README.md", "README.md"})


def safe_path(path: str) -> bool:
    parts = PurePosixPath(path).parts
    return bool(parts) and not path.startswith("/") and "\\" not in path and all(p not in (".", "..") for p in parts) and str(PurePosixPath(path)) == path


def allowed_source(path: str) -> bool:
    if not safe_path(path):
        return False
    if path in EXACT:
        return True
    if any(path.startswith(prefix) for prefix in ("book_core/", "runtime/", "app/api/", "app/study/")):
        return path.endswith(".py") and "/__pycache__/" not in path
    if path.startswith("app/web/src/"):
        return path.endswith((".ts", ".tsx", ".css"))
    if path.startswith("app/web/pilot/"):
        return path.endswith(".spec.ts")
    if path.startswith("app/web/public/licenses/"):
        return path.endswith(".txt")
    return False


def git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), *args])


def source_files(root: Path, ref: str) -> tuple[str, dict[str, tuple[int, bytes]]]:
    # No revision expressions supplied by callers; HEAD or an exact commit ID only.
    if ref != "HEAD" and not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", ref):
        raise ValueError("use HEAD or an exact commit SHA")
    commit = git(root, "rev-parse", "--verify", f"{ref}^{{commit}}").decode().strip()
    files: dict[str, tuple[int, bytes]] = {}
    total = 0
    for entry in git(root, "ls-tree", "-rlz", commit).split(b"\0"):
        if not entry:
            continue
        descriptor, raw_path = entry.split(b"\t", 1)
        mode, kind, oid, size = descriptor.decode().split()
        path = raw_path.decode("utf-8")
        if path == "README.md" or not allowed_source(path):
            continue
        if kind != "blob" or mode not in ("100644", "100755"):
            raise ValueError(f"non-regular source entry: {path}")
        count = int(size)
        total += count
        if count > MAX_FILE_BYTES or total > MAX_TOTAL_BYTES or len(files) >= MAX_FILES:
            raise ValueError("source exceeds size/count budget")
        data = git(root, "cat-file", "blob", oid)
        if len(data) != count:
            raise ValueError("Git blob size mismatch")
        files[path] = (0o755 if mode == "100755" else 0o644, data)
    if README_SOURCE in files:
        files["README.md"] = files[README_SOURCE]
    validate_files(files)
    return commit, files


def validate_files(files: dict[str, tuple[int, bytes]]) -> None:
    if not REQUIRED <= files.keys() or len(files) > MAX_FILES:
        raise ValueError("missing required source or too many files")
    if any(not allowed_source(path) or mode not in (0o644, 0o755) or len(data) > MAX_FILE_BYTES
           for path, (mode, data) in files.items()):
        raise ValueError("unexpected source path, mode or file size")
    if files["README.md"] != files[README_SOURCE]:
        raise ValueError("root README must preserve its declared source alias")
    if sum(len(data) for _, data in files.values()) > MAX_TOTAL_BYTES:
        raise ValueError("source payload too large")


def manifest_bytes(commit: str, files: dict[str, tuple[int, bytes]]) -> bytes:
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", commit):
        raise ValueError("invalid source commit")
    return (json.dumps({"schema_version": "book_reader_pilot_source_v1", "source_commit": commit,
        "files": [{"path": path, "source_path": README_SOURCE if path == "README.md" else path,
                   "mode": mode, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
                  for path, (mode, data) in sorted(files.items())]}, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def tar_bytes(commit: str, files: dict[str, tuple[int, bytes]]) -> bytes:
    validate_files(files)
    entries = {**files, MANIFEST: (0o644, manifest_bytes(commit, files))}
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for path, (mode, data) in sorted(entries.items()):
            info = tarfile.TarInfo(f"{ROOT}/{path}")
            info.size, info.mode, info.mtime = len(data), mode, 0
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            archive.addfile(info, io.BytesIO(data))
    return output.getvalue()


def archive_bytes(commit: str, files: dict[str, tuple[int, bytes]]) -> bytes:
    output = io.BytesIO()
    with gzip.GzipFile(fileobj=output, filename="", mode="wb", mtime=0, compresslevel=9) as compressed:
        compressed.write(tar_bytes(commit, files))
    return output.getvalue()


def verify_archive(path: Path) -> tuple[str, dict[str, tuple[int, bytes]], bytes]:
    if not path.is_file() or path.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ValueError("archive too large")
    with path.open("rb") as source:
        archive_data = source.read(MAX_ARCHIVE_BYTES + 1)
    if len(archive_data) > MAX_ARCHIVE_BYTES:
        raise ValueError("archive grew beyond byte budget")
    # One bounded gzip member, no optional filename/comment/extra metadata.
    if archive_data[:10] != bytes.fromhex("1f8b08000000000002ff"):
        raise ValueError("unexpected gzip metadata")
    decoder = zlib.decompressobj(wbits=31)
    tar_data = decoder.decompress(archive_data, MAX_TAR_BYTES + 1)
    if len(tar_data) > MAX_TAR_BYTES or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        raise ValueError("oversized, incomplete or trailing gzip payload")
    files: dict[str, tuple[int, bytes]] = {}
    total = 0
    with tarfile.open(fileobj=io.BytesIO(tar_data), mode="r:") as archive:
        for info in archive:
            if len(files) >= MAX_FILES + 1 or not info.isreg() or not info.name.startswith(f"{ROOT}/"):
                raise ValueError("unexpected archive member")
            name = info.name[len(ROOT) + 1:]
            if not safe_path(name) or name in files or (name != MANIFEST and not allowed_source(name)):
                raise ValueError("unexpected or duplicate path")
            if info.size < 0 or info.size > MAX_FILE_BYTES or info.mode not in (0o644, 0o755):
                raise ValueError("invalid member size or permissions")
            total += info.size
            if total > MAX_TOTAL_BYTES + MAX_FILE_BYTES:
                raise ValueError("archive payload too large")
            stream = archive.extractfile(info)
            if stream is None:
                raise ValueError("missing member data")
            data = stream.read(info.size + 1)
            if len(data) != info.size:
                raise ValueError("truncated archive member")
            files[name] = (info.mode, data)
    raw_manifest = files.pop(MANIFEST, (0, b""))[1]
    manifest = json.loads(raw_manifest)
    commit = manifest["source_commit"]
    validate_files(files)
    # Canonical encoding also rejects unknown fields, changed modes, duplicates,
    # renamed files, size/hash mismatches and altered manifest records.
    if manifest_bytes(commit, files) != raw_manifest:
        raise ValueError("manifest does not bind exact source files")
    if tar_data != tar_bytes(commit, files):
        raise ValueError("noncanonical TAR metadata or trailing data")
    return commit, files, raw_manifest


def extract_archive(path: Path, destination: Path) -> None:
    _, files, manifest = verify_archive(path)  # Verify everything before creating output.
    destination.mkdir(parents=True, exist_ok=False)
    for name, (mode, data) in {**files, MANIFEST: (0o644, manifest)}.items():
        output = destination / name
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(data)
        output.chmod(mode)


def directory_files(root: Path) -> tuple[str, dict[str, tuple[int, bytes]]]:
    root = root.resolve()
    manifest_path = root / MANIFEST
    if manifest_path.is_symlink() or not manifest_path.is_file() or manifest_path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("invalid manifest file")
    with manifest_path.open("rb") as stream:
        manifest_raw = stream.read(MAX_FILE_BYTES + 1)
    if len(manifest_raw) > MAX_FILE_BYTES:
        raise ValueError("manifest grew beyond byte budget")
    manifest = json.loads(manifest_raw)
    rows = manifest["files"]
    if not isinstance(rows, list) or len(rows) > MAX_FILES:
        raise ValueError("invalid manifest entries")
    files: dict[str, tuple[int, bytes]] = {}
    total = 0
    for row in rows:
        name = row["path"]
        if not isinstance(name, str) or not allowed_source(name) or name in files:
            raise ValueError("invalid manifest path")
        path = root / name
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root) or path.stat().st_size > MAX_FILE_BYTES:
            raise ValueError("invalid source file")
        if total + path.stat().st_size > MAX_TOTAL_BYTES:
            raise ValueError("source directory exceeds byte budget")
        with path.open("rb") as stream:
            data = stream.read(min(MAX_FILE_BYTES + 1, MAX_TOTAL_BYTES - total + 1))
        if len(data) > MAX_FILE_BYTES or total + len(data) > MAX_TOTAL_BYTES:
            raise ValueError("source file grew beyond byte budget")
        total += len(data)
        files[name] = (row["mode"], data)
    validate_files(files)
    if manifest_bytes(manifest["source_commit"], files) != manifest_raw:
        raise ValueError("source directory has changed")
    return manifest["source_commit"], files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("--repository", type=Path, default=Path.cwd())
    build.add_argument("--ref", default="HEAD")
    build.add_argument("--output", type=Path, required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("archive", type=Path)
    extract = sub.add_parser("extract")
    extract.add_argument("archive", type=Path)
    extract.add_argument("destination", type=Path)
    repack = sub.add_parser("repack")
    repack.add_argument("directory", type=Path)
    repack.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command in ("build", "repack"):
        commit, files = source_files(args.repository, args.ref) if args.command == "build" else directory_files(args.directory)
        data = archive_bytes(commit, files)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as out:
            out.write(data)
        print(json.dumps({"source_commit": commit, "file_count": len(files), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}))
    elif args.command == "verify":
        commit, files, _ = verify_archive(args.archive)
        print(json.dumps({"source_commit": commit, "file_count": len(files), "verified": True,
                          "sha256": hashlib.sha256(args.archive.read_bytes()).hexdigest()}))
    else:
        extract_archive(args.archive, args.destination)
        print(json.dumps({"extracted": str(args.destination)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
