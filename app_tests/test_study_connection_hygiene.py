from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.study.repository import StudyRecordRepository


class TrackingStudyRecordRepository(StudyRecordRepository):
    def __init__(self, db_path: Path) -> None:
        self.connections: list[sqlite3.Connection] = []
        super().__init__(db_path)

    def _connect(self) -> sqlite3.Connection:
        connection = super()._connect()
        self.connections.append(connection)
        return connection


class StudyRecordConnectionHygieneTests(unittest.TestCase):
    def assert_connection_closed(self, connection: sqlite3.Connection) -> None:
        with self.assertRaises(sqlite3.ProgrammingError):
            connection.execute("SELECT 1")

    def test_all_public_read_paths_close_their_sqlite_connections(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = TrackingStudyRecordRepository(
                Path(temp_dir) / "book-app.sqlite3"
            )

            for connection in repository.connections:
                self.assert_connection_closed(connection)
            repository.connections.clear()

            repository.get_profile_id()
            self.assertEqual(len(repository.connections), 1)
            self.assert_connection_closed(repository.connections[-1])

            repository.touch_record(
                "course-a",
                "book-a",
                "section-a",
                "learn",
            )
            for connection in repository.connections:
                self.assert_connection_closed(connection)
            repository.connections.clear()

            repository.get_record("course-a", "section-a", "learn")
            for connection in repository.connections:
                self.assert_connection_closed(connection)
            repository.connections.clear()

            repository.list_course_records("course-a")
            for connection in repository.connections:
                self.assert_connection_closed(connection)
            repository.connections.clear()

            repository.get_recent_record()
            for connection in repository.connections:
                self.assert_connection_closed(connection)


if __name__ == "__main__":
    unittest.main()
