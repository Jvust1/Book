from __future__ import annotations

import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID, uuid4

from app.study.paths import resolve_study_db_path
from app.study.repository import StudyRecordRepository


class StudyRecordRepositoryFoundationTests(unittest.TestCase):
    def test_data_dir_override_is_deterministic(self) -> None:
        path = resolve_study_db_path(
            environ={"BOOK_APP_DATA_DIR": "/tmp/book-data"},
            home=Path("/ignored"),
        )

        self.assertEqual(path, Path("/tmp/book-data") / "book-app.sqlite3")

    def test_first_open_creates_one_stable_profile_uuid(self) -> None:
        with TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "nested" / "study.sqlite3"

            first = StudyRecordRepository(db_path).get_profile_id()
            second = StudyRecordRepository(db_path).get_profile_id()

            self.assertTrue(db_path.exists())
            self.assertEqual(first, second)
            self.assertEqual(str(UUID(first)), first)

    def test_schema_rejects_invalid_record_constraints(self) -> None:
        with TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "study.sqlite3"
            profile_id = StudyRecordRepository(db_path).get_profile_id()

            invalid_cases = (
                {"mode": "watch"},
                {"status": "paused"},
                {"progress": 50},
                {"revision": 0},
                {"sync_status": "pending"},
            )
            for index, overrides in enumerate(invalid_cases):
                with self.subTest(overrides=overrides):
                    values = self._record_values(
                        profile_id=profile_id,
                        section_id=f"invalid-{index}",
                        **overrides,
                    )
                    with sqlite3.connect(db_path) as connection:
                        with self.assertRaises(sqlite3.IntegrityError):
                            self._insert_record(connection, values)

    def test_schema_rejects_duplicate_logical_record(self) -> None:
        with TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "study.sqlite3"
            profile_id = StudyRecordRepository(db_path).get_profile_id()
            first = self._record_values(profile_id=profile_id)
            duplicate = self._record_values(profile_id=profile_id)

            with sqlite3.connect(db_path) as connection:
                self._insert_record(connection, first)
                connection.commit()
                with self.assertRaises(sqlite3.IntegrityError):
                    self._insert_record(connection, duplicate)

    @staticmethod
    def _record_values(
        *,
        profile_id: str,
        section_id: str = "ch01_s01",
        mode: str = "learn",
        status: str = "in_progress",
        progress: int = 0,
        revision: int = 1,
        sync_status: str = "local",
    ) -> tuple[object, ...]:
        timestamp = "2026-08-28T01:00:00+00:00"
        return (
            str(uuid4()),
            profile_id,
            "functional_analysis_course",
            "stein_shakarchi_functional_analysis_2011",
            section_id,
            mode,
            status,
            progress,
            timestamp,
            timestamp,
            None,
            timestamp,
            timestamp,
            revision,
            None,
            sync_status,
        )

    @staticmethod
    def _insert_record(
        connection: sqlite3.Connection,
        values: tuple[object, ...],
    ) -> None:
        connection.execute(
            """
            INSERT INTO study_records (
                study_record_id,
                profile_id,
                course_id,
                book_id,
                section_id,
                mode,
                status,
                progress,
                started_at,
                last_studied_at,
                completed_at,
                created_at,
                updated_at,
                revision,
                deleted_at,
                sync_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            values,
        )


if __name__ == "__main__":
    unittest.main()
