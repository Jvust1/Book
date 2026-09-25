from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from app.study.repository import StudyRecord, StudyRecordRepository


class StudyRecordSyncTimestampTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repository = StudyRecordRepository(Path(self.tmp.name) / "study.sqlite3")

    @staticmethod
    def record(section_id: str, timestamp: str) -> StudyRecord:
        return StudyRecord(
            study_record_id="external-record",
            profile_id="external-profile",
            course_id="course",
            book_id="book",
            section_id=section_id,
            mode="learn",
            status="completed",
            progress=100,
            started_at=timestamp,
            last_studied_at=timestamp,
            completed_at=timestamp,
            created_at=timestamp,
            updated_at=timestamp,
            revision=1,
            deleted_at=None,
            sync_status="local",
        )

    def test_import_orders_activity_by_instant_across_timezones(self) -> None:
        older = self.record("older", "2026-09-22T12:00:00+08:00")
        newer = self.record("newer", "2026-09-22T05:00:00+00:00")

        self.assertEqual(self.repository.merge_records((older, newer)), 2)

        self.assertEqual(self.repository.get_recent_record().section_id, "newer")
        self.assertEqual(
            [row.section_id for row in self.repository.list_course_records("course")],
            ["newer", "older"],
        )
        self.assertEqual(
            [row.section_id for row in self.repository.list_all_records()],
            ["newer", "older"],
        )
        stored = self.repository.get_record("course", "older", "learn")
        for field in (
            "started_at", "last_studied_at", "completed_at", "created_at", "updated_at"
        ):
            self.assertEqual(getattr(stored, field), "2026-09-22T04:00:00+00:00")
        self.assertEqual(older.updated_at, "2026-09-22T12:00:00+08:00")

    def test_update_normalizes_timestamps_and_duplicate_import_is_noop(self) -> None:
        original = self.record("same", "2026-09-22T04:00:00+00:00")
        self.repository.merge_records((original,))
        local_id = self.repository.get_record("course", "same", "learn").study_record_id
        incoming = replace(
            self.record("same", "2026-09-22T00:00:00.123456-05:00"),
            status="in_progress",
            progress=0,
            completed_at=None,
            revision=7,
        )

        self.assertEqual(self.repository.merge_records((incoming,)), 1)
        updated = self.repository.get_record("course", "same", "learn")

        self.assertEqual(updated.study_record_id, local_id)
        self.assertEqual(updated.updated_at, "2026-09-22T05:00:00.123456+00:00")
        self.assertEqual(updated.last_studied_at, updated.updated_at)
        self.assertEqual(updated.started_at, updated.updated_at)
        self.assertEqual(updated.created_at, updated.updated_at)
        self.assertIsNone(updated.completed_at)
        self.assertEqual(updated.revision, 7)
        self.assertEqual(self.repository.merge_records((incoming, original)), 0)
        self.assertEqual(self.repository.get_record("course", "same", "learn"), updated)

    def test_utc_z_suffix_does_not_hide_later_fractional_activity(self) -> None:
        older = self.record("older", "2026-09-22T05:00:00Z")
        newer = self.record("newer", "2026-09-22T05:00:00.000001+00:00")

        self.repository.merge_records((older, newer))

        self.assertEqual(self.repository.get_recent_record().section_id, "newer")
        self.assertEqual(self.repository.list_all_records()[0].section_id, "newer")


if __name__ == "__main__":
    unittest.main()
