"""Only original tiny sentinels are used for archive safety/reproducibility checks."""
import gzip
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
import zlib
from unittest.mock import patch

from tools import build_reader_pilot_source as bundle

COMMIT = "a" * 40


def fixtures():
    files = {path: (0o644, f"original fixture for {path}\n".encode()) for path in bundle.REQUIRED}
    files["README.md"] = files[bundle.README_SOURCE]
    return files


def forge(entries):
    output = io.BytesIO()
    with gzip.GzipFile(fileobj=output, filename="", mode="wb", mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w") as archive:
            for name, data, kind in entries:
                info = tarfile.TarInfo(name)
                info.mode, info.size, info.type = 0o644, len(data), kind
                if kind == tarfile.SYMTYPE:
                    info.linkname = "../../outside"
                archive.addfile(info, io.BytesIO(data))
    return output.getvalue()


class ReaderPilotSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.archive = self.root / "source.tar.gz"
        self.files = fixtures()

    def test_build_verify_extract_repack_are_byte_identical(self):
        data = bundle.archive_bytes(COMMIT, self.files)
        self.assertEqual(data, bundle.archive_bytes(COMMIT, dict(reversed(list(self.files.items())))))
        self.archive.write_bytes(data)
        commit, verified, _ = bundle.verify_archive(self.archive)
        self.assertEqual(commit, COMMIT)
        self.assertEqual(verified, self.files)
        dest = self.root / "extracted"
        bundle.extract_archive(self.archive, dest)
        rebuilt_commit, rebuilt = bundle.directory_files(dest)
        self.assertEqual(data, bundle.archive_bytes(rebuilt_commit, rebuilt))
        with tarfile.open(self.archive) as archive:
            for member in archive:
                self.assertEqual((member.uid, member.gid, member.mtime, member.uname, member.gname), (0, 0, 0, "", ""))

    def test_verification_does_not_depend_on_one_zlib_deflate_encoding(self):
        raw = bundle.tar_bytes(COMMIT, self.files)
        compressor = zlib.compressobj(level=9, wbits=31)
        halfway = len(raw) // 2
        encoded = compressor.compress(raw[:halfway]) + compressor.flush(zlib.Z_SYNC_FLUSH)
        encoded += compressor.compress(raw[halfway:]) + compressor.flush(zlib.Z_FINISH)
        # zlib's OS byte differs from the deliberately platform-neutral GzipFile header.
        encoded = encoded[:9] + b"\xff" + encoded[10:]
        self.assertNotEqual(encoded, bundle.archive_bytes(COMMIT, self.files))
        self.archive.write_bytes(encoded)
        self.assertEqual(bundle.verify_archive(self.archive)[1], self.files)

    def test_allows_code_and_complete_notices_but_excludes_data_and_credentials(self):
        for path in ["app/web/src/example.tsx", "runtime/example.py", "app/web/public/licenses/Example-LICENSE.txt",
                     "app/web/playwright.portable.config.ts"]:
            self.assertTrue(bundle.allowed_source(path), path)
        for path in ["books/original/chapter.txt", "courses/course/course.json", "library/library.json",
                     ".env", "app/api/.env", "app/api/credentials.json", "app/web/public/private.pdf",
                     "node_modules/example/index.js", "app/web/src/../../private.ts", "/runtime/file.py",
                     "runtime/./file.py", "runtime//file.py", "runtime/__pycache__/file.py", "runtime/file\\bad.py"]:
            self.assertFalse(bundle.allowed_source(path), path)

    def test_windows_unsafe_paths_fail_before_extraction(self):
        self.assertFalse(bundle.safe_path("runtime/bad\ud800.py"))
        bad = ["runtime/entry.py:alternate.py", "runtime/CON.py", "runtime/nUl.backup.py",
               "runtime/COM1.py", "runtime/lpt9.data.py", "runtime/COM¹.py", "runtime/LPT³.py",
               "runtime/folder. /entry.py", "runtime/folder./entry.py", "runtime/folder /entry.py",
               "runtime/a?b.py", "runtime/a*b.py", "runtime/a<b.py", "runtime/a|b.py",
               "runtime/zero\x00.py", "runtime/control\x1f.py", "runtime/" + "x" * 256 + ".py", "/runtime/file.py", "C:/runtime/file.py",
               "C:runtime/file.py", "//server/share/runtime/file.py", "\\\\server\\share\\file.py", "runtime/../escape.py"]
        for index, name in enumerate(bad):
            with self.subTest(path=name):
                self.assertFalse(bundle.allowed_source(name))
                files = {**self.files, name: (0o644, b"original")}
                # Forge an otherwise canonical archive solely to test verifier
                # rejection; the production path validator is never weakened.
                with patch.object(bundle, "validate_files", return_value=None):
                    self.archive.write_bytes(bundle.archive_bytes(COMMIT, files))
                dest = self.root / f"rejected-{index}"
                with self.assertRaises(ValueError):
                    bundle.extract_archive(self.archive, dest)
                self.assertFalse(dest.exists())

    def test_portable_path_collisions_fail_before_output(self):
        cases = [("runtime/Case.py", "runtime/case.py"),
                 ("runtime/Dir/first.py", "runtime/dir/second.py"),
                 ("runtime/file.py", "runtime/file.py/child.py"),
                 ("runtime/Folder.py/child.py", "runtime/folder.py")]
        for index, names in enumerate(cases):
            with self.subTest(paths=names):
                files = {**self.files, **{name: (0o644, b"original") for name in names}}
                with self.assertRaises(ValueError):
                    bundle.archive_bytes(COMMIT, files)
                with patch.object(bundle, "validate_files", return_value=None):
                    self.archive.write_bytes(bundle.archive_bytes(COMMIT, files))
                dest = self.root / f"collision-{index}"
                with self.assertRaises(ValueError):
                    bundle.extract_archive(self.archive, dest)
                self.assertFalse(dest.exists())

    def test_case_colliding_manifest_is_rejected_before_directory_reads(self):
        self.archive.write_bytes(bundle.archive_bytes(COMMIT, self.files))
        dest = self.root / "extracted"
        bundle.extract_archive(self.archive, dest)
        names = ("runtime/Case.py", "runtime/case.py")
        changed = {**self.files, **{name: (0o644, b"original") for name in names}}
        for name in names:
            file = dest / name
            file.parent.mkdir(exist_ok=True)
            file.write_bytes(b"original")
        (dest / bundle.MANIFEST).write_bytes(bundle.manifest_bytes(COMMIT, changed))
        original_open = Path.open
        # Match directory_files normalization (Windows temp paths may have aliases).
        allowed_manifest = (dest / bundle.MANIFEST).resolve()
        def guard_open(path, *args, **kwargs):
            if path != allowed_manifest:
                raise AssertionError("colliding manifest must fail before opening source files")
            return original_open(path, *args, **kwargs)
        with patch.object(Path, "open", guard_open), self.assertRaises(ValueError):
            bundle.directory_files(dest)

    def test_portable_unicode_and_spaces_remain_exact(self):
        name = "runtime/original space/原创😀.py"
        files = {**self.files, name: (0o644, b"original")}
        self.archive.write_bytes(bundle.archive_bytes(COMMIT, files))
        _, parsed, _ = bundle.verify_archive(self.archive)
        self.assertEqual(set(parsed), set(files))
        dest = self.root / "original path with spaces"
        bundle.extract_archive(self.archive, dest)
        self.assertEqual(bundle.directory_files(dest)[1], files)

    def test_missing_required_source_fails(self):
        self.files.pop(next(iter(bundle.REQUIRED)))
        with self.assertRaises(ValueError):
            bundle.archive_bytes(COMMIT, self.files)

    def test_size_and_count_limits_are_enforced_before_archive_creation(self):
        for setting, value in [("MAX_FILE_BYTES", 1), ("MAX_TOTAL_BYTES", 1), ("MAX_FILES", 1)]:
            with self.subTest(setting=setting), patch.object(bundle, setting, value), self.assertRaises(ValueError):
                bundle.archive_bytes(COMMIT, self.files)

    def test_archive_traversal_links_and_duplicates_are_rejected_before_extract(self):
        cases = [
            [(f"{bundle.ROOT}/../../escape", b"original", tarfile.REGTYPE)],
            [(f"{bundle.ROOT}/runtime/link.py", b"", tarfile.SYMTYPE)],
            [(f"{bundle.ROOT}/runtime/a.py", b"a", tarfile.REGTYPE)] * 2,
        ]
        for entries in cases:
            with self.subTest(entries=entries):
                self.archive.write_bytes(forge(entries))
                dest = self.root / "must-not-exist"
                with self.assertRaises(ValueError):
                    bundle.extract_archive(self.archive, dest)
                self.assertFalse(dest.exists())
        self.assertFalse((self.root / "escape").exists())

    def test_file_tampering_and_trailing_payload_are_rejected(self):
        manifest = bundle.manifest_bytes(COMMIT, self.files)
        changed = dict(self.files)
        path = next(iter(changed))
        changed[path] = (0o644, b"tampered original sentinel")
        entries = [(f"{bundle.ROOT}/{name}", data, tarfile.REGTYPE) for name, (_, data) in changed.items()]
        entries.append((f"{bundle.ROOT}/{bundle.MANIFEST}", manifest, tarfile.REGTYPE))
        self.archive.write_bytes(forge(entries))
        with self.assertRaises(ValueError):
            bundle.verify_archive(self.archive)
        self.archive.write_bytes(bundle.archive_bytes(COMMIT, self.files) + b"unlisted payload")
        with self.assertRaises((ValueError, tarfile.TarError, OSError)):
            bundle.verify_archive(self.archive)

    def test_changed_directory_cannot_claim_the_original_commit(self):
        self.archive.write_bytes(bundle.archive_bytes(COMMIT, self.files))
        dest = self.root / "extracted"
        bundle.extract_archive(self.archive, dest)
        (dest / next(iter(self.files))).write_bytes(b"changed")
        with self.assertRaises(ValueError):
            bundle.directory_files(dest)

    def test_does_not_overwrite_existing_extract_destination(self):
        self.archive.write_bytes(bundle.archive_bytes(COMMIT, self.files))
        dest = self.root / "existing"
        dest.mkdir()
        (dest / "keep").write_text("original")
        with self.assertRaises(FileExistsError):
            bundle.extract_archive(self.archive, dest)
        self.assertEqual((dest / "keep").read_text(), "original")

    def test_directory_symlinks_and_non_regular_files_are_rejected(self):
        self.archive.write_bytes(bundle.archive_bytes(COMMIT, self.files))
        dest = self.root / "extracted"
        bundle.extract_archive(self.archive, dest)
        target = dest / "runtime/symbolic_answer.py"
        target.unlink()
        outside = self.root / "outside-original.txt"
        outside.write_bytes(self.files["runtime/symbolic_answer.py"][1])
        target.symlink_to(outside)
        with self.assertRaises(ValueError):
            bundle.directory_files(dest)
        target.unlink()
        if hasattr(os, "mkfifo"):
            os.mkfifo(target)
            with self.assertRaises(ValueError):
                bundle.directory_files(dest)

    def test_directory_aggregate_budget_is_checked_during_read(self):
        self.archive.write_bytes(bundle.archive_bytes(COMMIT, self.files))
        dest = self.root / "extracted"
        bundle.extract_archive(self.archive, dest)
        with patch.object(bundle, "MAX_TOTAL_BYTES", 1), self.assertRaises(ValueError):
            bundle.directory_files(dest)

    def test_root_readme_alias_cannot_substitute_unlisted_document_content(self):
        self.files["README.md"] = (0o644, b"unlisted readme")
        with self.assertRaises(ValueError):
            bundle.archive_bytes(COMMIT, self.files)

    def _git_repo(self):
        repo = self.root / "repo"
        repo.mkdir()
        for path, (_, data) in self.files.items():
            file = repo / path
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(data)
        for path in ["books/private.pdf", "library/library.json", "courses/course.json", "app/api/.env"]:
            file = repo / path
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text("original exclusion sentinel")
        env = {**os.environ, "GIT_AUTHOR_NAME": "Original fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
               "GIT_COMMITTER_NAME": "Original fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid"}
        subprocess.run(["git", "init", "-q", str(repo)], check=True, env=env)
        subprocess.run(["git", "-C", str(repo), "add", "."], check=True, env=env)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "original fixture"], check=True, env=env)
        return repo, env

    def test_immutable_git_blobs_exclude_untracked_and_dirty_worktree_data(self):
        repo, _ = self._git_repo()
        path = next(iter(self.files))
        (repo / path).write_bytes(b"dirty data must not enter committed archive")
        commit, collected = bundle.source_files(repo, "HEAD")
        self.assertRegex(commit, r"^[0-9a-f]{40}$")
        self.assertEqual(collected, self.files)
        self.assertFalse(any(path.startswith(("books/", "library/", "courses/")) for path in collected))
        for ref in ["--help", "HEAD~1", "main"]:
            with self.assertRaises(ValueError):
                bundle.source_files(repo, ref)

    def test_legacy_v1_ref_without_portable_config_still_rebuilds_and_verifies(self):
        portable = "app/web/playwright.portable.config.ts"
        self.assertNotIn(portable, bundle.REQUIRED)
        repo, env = self._git_repo()
        old_commit, old_files = bundle.source_files(repo, "HEAD")
        self.assertNotIn(portable, old_files)
        old_bytes = bundle.archive_bytes(old_commit, old_files)
        self.archive.write_bytes(old_bytes)
        self.assertEqual(bundle.verify_archive(self.archive)[1], old_files)
        (repo / portable).write_bytes(b"original portable config fixture")
        subprocess.run(["git", "-C", str(repo), "add", portable], check=True, env=env)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "original portable addition"], check=True, env=env)
        _, current_files = bundle.source_files(repo, "HEAD")
        self.assertEqual(current_files[portable][1], b"original portable config fixture")
        rebuilt_commit, rebuilt_files = bundle.source_files(repo, old_commit)
        self.assertEqual(bundle.archive_bytes(rebuilt_commit, rebuilt_files), old_bytes)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink not supported")
    def test_selected_git_symlink_is_rejected(self):
        repo, env = self._git_repo()
        link = repo / "runtime" / "link.py"
        link.parent.mkdir(exist_ok=True)
        link.symlink_to("../books/private.pdf")
        subprocess.run(["git", "-C", str(repo), "add", "."], check=True, env=env)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "link fixture"], check=True, env=env)
        with self.assertRaises(ValueError):
            bundle.source_files(repo, "HEAD")


if __name__ == "__main__":
    unittest.main()
