from __future__ import annotations

import sqlite3
import unittest
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID, uuid4

from app.study.paths import resolve_study_db_path
from app.study.repository import StudyRecordRepository


class _Clock:
    def __init__(self) -> None:
        self._value = datetime(2026, 8, 28, 1, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        value = self._value
        self._value += timedelta(minutes=1)
        return value


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
                    with closing(sqlite3.connect(db_path)) as connection:
                        with self.assertRaises(sqlite3.IntegrityError):
                            self._insert_record(connection, values)

    def test_schema_rejects_duplicate_logical_record(self) -> None:
        with TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "study.sqlite3"
            profile_id = StudyRecordRepository(db_path).get_profile_id()
            first = self._record_values(profile_id=profile_id)
            duplicate = self._record_values(profile_id=profile_id)

            with closing(sqlite3.connect(db_path)) as connection:
                self._insert_record(connection, first)
                connection.commit()
                with self.assertRaises(sqlite3.IntegrityError):
                    self._insert_record(connection, duplicate)

    def test_schema_permits_same_logical_scope_for_different_profiles(self) -> None:
        with TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "study.sqlite3"
            repo = StudyRecordRepository(db_path)
            first = self._record_values(profile_id=repo.get_profile_id())
            second = self._record_values(profile_id=str(uuid4()))

            with closing(sqlite3.connect(db_path)) as connection:
                self._insert_record(connection, first)
                self._insert_record(connection, second)
                connection.commit()
                count = connection.execute(
                    "SELECT COUNT(*) FROM study_records"
                ).fetchone()[0]

            self.assertEqual(count, 2)

    @staticmethod
    def _record_values(
        *,
        profile_id: str,
        course_id: str = "functional_analysis_course",
        section_id: str = "ch01_s01",
        mode: str = "learn",
        status: str = "in_progress",
        progress: int = 0,
        revision: int = 1,
        deleted_at: str | None = None,
        sync_status: str = "local",
    ) -> tuple[object, ...]:
        timestamp = "2026-08-28T01:00:00+00:00"
        return (
            str(uuid4()),
            profile_id,
            course_id,
            "stein_shakarchi_functional_analysis_2011",
            section_id,
            mode,
            status,
            progress,
            timestamp,
            timestamp,
            timestamp if status == "completed" else None,
            timestamp,
            timestamp,
            revision,
            deleted_at,
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


class StudyRecordRepositoryBehaviorTests(unittest.TestCase):
    COURSE_ID = "functional_analysis_course"
    BOOK_ID = "stein_shakarchi_functional_analysis_2011"
    SECTION_ID = "ch01_s01"

    def setUp(self) -> None:
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db_path = Path(self.temp.name) / "study.sqlite3"
        self.clock = _Clock()
        self.repo = StudyRecordRepository(self.db_path, now=self.clock)

    def touch(self, *, section_id: str | None = None, mode: str = "learn"):
        return self.repo.touch_record(
            self.COURSE_ID,
            self.BOOK_ID,
            section_id or self.SECTION_ID,
            mode,
        )

    def complete(self, *, section_id: str | None = None, mode: str = "learn"):
        return self.repo.complete_record(
            self.COURSE_ID,
            self.BOOK_ID,
            section_id or self.SECTION_ID,
            mode,
        )

    def test_get_record_returns_none_before_first_touch(self) -> None:
        self.assertIsNone(
            self.repo.get_record(self.COURSE_ID, self.SECTION_ID, "learn")
        )

    def test_first_touch_creates_one_in_progress_record(self) -> None:
        record = self.touch()

        self.assertEqual(record.profile_id, self.repo.get_profile_id())
        self.assertEqual(record.course_id, self.COURSE_ID)
        self.assertEqual(record.book_id, self.BOOK_ID)
        self.assertEqual(record.section_id, self.SECTION_ID)
        self.assertEqual(record.mode, "learn")
        self.assertEqual(record.status, "in_progress")
        self.assertEqual(record.progress, 0)
        self.assertEqual(record.revision, 1)
        self.assertIsNone(record.completed_at)
        self.assertEqual(record.started_at, record.last_studied_at)
        self.assertEqual(record.created_at, record.updated_at)
        self.assertEqual(record.sync_status, "local")
        self.assertEqual(str(UUID(record.study_record_id)), record.study_record_id)

    def test_second_touch_updates_same_row_and_preserves_started_at(self) -> None:
        first = self.touch()
        second = self.touch()

        self.assertEqual(second.study_record_id, first.study_record_id)
        self.assertEqual(second.revision, 2)
        self.assertEqual(second.started_at, first.started_at)
        self.assertGreater(second.last_studied_at, first.last_studied_at)
        self.assertGreater(second.updated_at, first.updated_at)

    def test_complete_after_touch_sets_completed_state(self) -> None:
        first = self.touch()
        completed = self.complete()

        self.assertEqual(completed.study_record_id, first.study_record_id)
        self.assertEqual(completed.status, "completed")
        self.assertEqual(completed.progress, 100)
        self.assertIsNotNone(completed.completed_at)
        self.assertEqual(completed.revision, 2)
        self.assertGreater(completed.last_studied_at, first.last_studied_at)

    def test_direct_complete_creates_one_completed_record(self) -> None:
        completed = self.complete()

        self.assertEqual(completed.status, "completed")
        self.assertEqual(completed.progress, 100)
        self.assertEqual(completed.revision, 1)
        self.assertEqual(completed.started_at, completed.completed_at)
        self.assertEqual(completed.last_studied_at, completed.completed_at)

    def test_duplicate_complete_is_idempotent_without_revision_churn(self) -> None:
        first = self.complete()
        second = self.complete()

        self.assertEqual(second, first)

    def test_touching_completed_record_preserves_completion_and_advances_activity(self) -> None:
        completed = self.complete()
        reopened = self.touch()

        self.assertEqual(reopened.study_record_id, completed.study_record_id)
        self.assertEqual(reopened.status, "completed")
        self.assertEqual(reopened.progress, 100)
        self.assertEqual(reopened.completed_at, completed.completed_at)
        self.assertEqual(reopened.started_at, completed.started_at)
        self.assertEqual(reopened.revision, completed.revision + 1)
        self.assertGreater(reopened.last_studied_at, completed.last_studied_at)

    def test_four_modes_are_independent_rows(self) -> None:
        records = [
            self.touch(mode=mode)
            for mode in ("preview", "learn", "review", "practice")
        ]
        completed = self.complete(mode="learn")

        self.assertEqual(len({record.study_record_id for record in records}), 4)
        self.assertEqual(completed.status, "completed")
        for mode in ("preview", "review", "practice"):
            record = self.repo.get_record(self.COURSE_ID, self.SECTION_ID, mode)
            self.assertIsNotNone(record)
            self.assertEqual(record.status, "in_progress")
            self.assertEqual(record.progress, 0)

    def test_same_mode_in_two_sections_is_independent(self) -> None:
        first = self.touch(section_id="ch01_s01")
        second = self.touch(section_id="ch01_s02")

        self.assertNotEqual(first.study_record_id, second.study_record_id)
        self.assertEqual(first.mode, second.mode)
        self.assertNotEqual(first.section_id, second.section_id)

    def test_recent_record_uses_latest_last_studied_at(self) -> None:
        self.touch(section_id="ch01_s01", mode="preview")
        latest = self.touch(section_id="ch01_s02", mode="review")

        self.assertEqual(self.repo.get_recent_record(), latest)

    def test_list_course_records_filters_other_course_and_deleted_rows(self) -> None:
        kept = self.touch(section_id="ch01_s01", mode="preview")
        deleted = self.touch(section_id="ch01_s02", mode="learn")
        other_course = self.repo.touch_record(
            "other_course",
            "other_book",
            "other_section",
            "review",
        )
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute(
                "UPDATE study_records SET deleted_at = ? WHERE study_record_id = ?",
                ("2026-08-28T02:00:00+00:00", deleted.study_record_id),
            )
            connection.commit()

        records = self.repo.list_course_records(self.COURSE_ID)

        self.assertEqual(records, (kept,))
        self.assertNotIn(deleted, records)
        self.assertNotIn(other_course, records)


if __name__ == "__main__":
    unittest.main()