from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from uuid import UUID, uuid4


@dataclass(frozen=True)
class StudyRecord:
    study_record_id: str
    profile_id: str
    course_id: str
    book_id: str
    section_id: str
    mode: str
    status: str
    progress: int
    started_at: str
    last_studied_at: str
    completed_at: str | None
    created_at: str
    updated_at: str
    revision: int
    deleted_at: str | None
    sync_status: str


class StudyRecordRepositoryError(RuntimeError):
    """Base error for durable StudyRecord storage failures."""


class CorruptProfileError(StudyRecordRepositoryError):
    """Raised when the persisted hidden profile identity is invalid."""


class StudyRecordRepository:
    def __init__(
        self,
        db_path: Path,
        *,
        now: Callable[[], datetime] | None = None,
        uuid_factory: Callable[[], object] | None = None,
    ) -> None:
        self._db_path = Path(db_path)
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._uuid_factory = uuid_factory or uuid4
        self._initialize()

    @property
    def db_path(self) -> Path:
        return self._db_path

    def get_profile_id(self) -> str:
        try:
            with self._connect() as connection:
                row = connection.execute(
                    "SELECT profile_id FROM app_profile WHERE singleton = 1"
                ).fetchone()
        except sqlite3.Error as exc:
            raise StudyRecordRepositoryError(
                "Unable to read the local study profile"
            ) from exc

        if row is None:
            raise CorruptProfileError("Local study profile is missing")
        return self._validate_profile_id(str(row["profile_id"]))

    def get_record(
        self,
        course_id: str,
        section_id: str,
        mode: str,
    ) -> StudyRecord | None:
        profile_id = self.get_profile_id()
        try:
            with self._connect() as connection:
                row = connection.execute(
                    """
                    SELECT *
                    FROM study_records
                    WHERE profile_id = ?
                      AND course_id = ?
                      AND section_id = ?
                      AND mode = ?
                      AND deleted_at IS NULL
                    """,
                    (profile_id, course_id, section_id, mode),
                ).fetchone()
        except sqlite3.Error as exc:
            raise StudyRecordRepositoryError(
                "Unable to read the local study record"
            ) from exc
        return None if row is None else self._record_from_row(row)

    def touch_record(
        self,
        course_id: str,
        book_id: str,
        section_id: str,
        mode: str,
    ) -> StudyRecord:
        profile_id = self.get_profile_id()
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = self._select_logical_record(
                connection,
                profile_id,
                course_id,
                section_id,
                mode,
            )
            timestamp = self._timestamp()
            if row is None:
                study_record_id = self._new_uuid()
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
                    (
                        study_record_id,
                        profile_id,
                        course_id,
                        book_id,
                        section_id,
                        mode,
                        "in_progress",
                        0,
                        timestamp,
                        timestamp,
                        None,
                        timestamp,
                        timestamp,
                        1,
                        None,
                        "local",
                    ),
                )
            else:
                study_record_id = str(row["study_record_id"])
                connection.execute(
                    """
                    UPDATE study_records
                    SET last_studied_at = ?,
                        updated_at = ?,
                        revision = revision + 1
                    WHERE study_record_id = ?
                    """,
                    (timestamp, timestamp, study_record_id),
                )

            result = self._select_record_by_id(connection, study_record_id)
            connection.commit()
            return self._record_from_row(result)
        except StudyRecordRepositoryError:
            connection.rollback()
            raise
        except sqlite3.Error as exc:
            connection.rollback()
            raise StudyRecordRepositoryError(
                "Unable to save the local study record"
            ) from exc
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def complete_record(
        self,
        course_id: str,
        book_id: str,
        section_id: str,
        mode: str,
    ) -> StudyRecord:
        profile_id = self.get_profile_id()
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = self._select_logical_record(
                connection,
                profile_id,
                course_id,
                section_id,
                mode,
            )
            if row is not None and str(row["status"]) == "completed":
                connection.commit()
                return self._record_from_row(row)

            timestamp = self._timestamp()
            if row is None:
                study_record_id = self._new_uuid()
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
                    (
                        study_record_id,
                        profile_id,
                        course_id,
                        book_id,
                        section_id,
                        mode,
                        "completed",
                        100,
                        timestamp,
                        timestamp,
                        timestamp,
                        timestamp,
                        timestamp,
                        1,
                        None,
                        "local",
                    ),
                )
            else:
                study_record_id = str(row["study_record_id"])
                connection.execute(
                    """
                    UPDATE study_records
                    SET status = 'completed',
                        progress = 100,
                        completed_at = ?,
                        last_studied_at = ?,
                        updated_at = ?,
                        revision = revision + 1
                    WHERE study_record_id = ?
                    """,
                    (timestamp, timestamp, timestamp, study_record_id),
                )

            result = self._select_record_by_id(connection, study_record_id)
            connection.commit()
            return self._record_from_row(result)
        except StudyRecordRepositoryError:
            connection.rollback()
            raise
        except sqlite3.Error as exc:
            connection.rollback()
            raise StudyRecordRepositoryError(
                "Unable to complete the local study record"
            ) from exc
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def list_course_records(self, course_id: str) -> tuple[StudyRecord, ...]:
        profile_id = self.get_profile_id()
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT *
                    FROM study_records
                    WHERE profile_id = ?
                      AND course_id = ?
                      AND deleted_at IS NULL
                    ORDER BY last_studied_at DESC, updated_at DESC
                    """,
                    (profile_id, course_id),
                ).fetchall()
        except sqlite3.Error as exc:
            raise StudyRecordRepositoryError(
                "Unable to list local study records"
            ) from exc
        return tuple(self._record_from_row(row) for row in rows)

    def get_recent_record(self) -> StudyRecord | None:
        profile_id = self.get_profile_id()
        try:
            with self._connect() as connection:
                row = connection.execute(
                    """
                    SELECT *
                    FROM study_records
                    WHERE profile_id = ?
                      AND deleted_at IS NULL
                    ORDER BY last_studied_at DESC, updated_at DESC
                    LIMIT 1
                    """,
                    (profile_id,),
                ).fetchone()
        except sqlite3.Error as exc:
            raise StudyRecordRepositoryError(
                "Unable to read recent local study activity"
            ) from exc
        return None if row is None else self._record_from_row(row)

    def _initialize(self) -> None:
        try:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            connection = self._connect()
            try:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS app_profile (
                        singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                        profile_id TEXT NOT NULL UNIQUE,
                        created_at TEXT NOT NULL
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS study_records (
                        study_record_id TEXT PRIMARY KEY,
                        profile_id TEXT NOT NULL,
                        course_id TEXT NOT NULL,
                        book_id TEXT NOT NULL,
                        section_id TEXT NOT NULL,
                        mode TEXT NOT NULL CHECK (
                            mode IN ('preview','learn','review','practice')
                        ),
                        status TEXT NOT NULL CHECK (
                            status IN ('in_progress','completed')
                        ),
                        progress INTEGER NOT NULL CHECK (progress IN (0,100)),
                        started_at TEXT NOT NULL,
                        last_studied_at TEXT NOT NULL,
                        completed_at TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        revision INTEGER NOT NULL CHECK (revision >= 1),
                        deleted_at TEXT,
                        sync_status TEXT NOT NULL CHECK (sync_status = 'local'),
                        UNIQUE (profile_id, course_id, section_id, mode)
                    )
                    """
                )

                row = connection.execute(
                    "SELECT profile_id FROM app_profile WHERE singleton = 1"
                ).fetchone()
                if row is None:
                    profile_id = self._validate_profile_id(str(self._uuid_factory()))
                    connection.execute(
                        """
                        INSERT INTO app_profile (singleton, profile_id, created_at)
                        VALUES (1, ?, ?)
                        """,
                        (profile_id, self._timestamp()),
                    )
                else:
                    self._validate_profile_id(str(row["profile_id"]))
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                connection.close()
        except StudyRecordRepositoryError:
            raise
        except (OSError, sqlite3.Error) as exc:
            raise StudyRecordRepositoryError(
                "Unable to initialize the local study store"
            ) from exc

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._db_path, isolation_level=None)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _select_logical_record(
        connection: sqlite3.Connection,
        profile_id: str,
        course_id: str,
        section_id: str,
        mode: str,
    ) -> sqlite3.Row | None:
        return connection.execute(
            """
            SELECT *
            FROM study_records
            WHERE profile_id = ?
              AND course_id = ?
              AND section_id = ?
              AND mode = ?
              AND deleted_at IS NULL
            """,
            (profile_id, course_id, section_id, mode),
        ).fetchone()

    @staticmethod
    def _select_record_by_id(
        connection: sqlite3.Connection,
        study_record_id: str,
    ) -> sqlite3.Row:
        row = connection.execute(
            "SELECT * FROM study_records WHERE study_record_id = ?",
            (study_record_id,),
        ).fetchone()
        if row is None:
            raise StudyRecordRepositoryError(
                "Local study record disappeared during mutation"
            )
        return row

    @staticmethod
    def _record_from_row(row: sqlite3.Row) -> StudyRecord:
        return StudyRecord(
            study_record_id=str(row["study_record_id"]),
            profile_id=str(row["profile_id"]),
            course_id=str(row["course_id"]),
            book_id=str(row["book_id"]),
            section_id=str(row["section_id"]),
            mode=str(row["mode"]),
            status=str(row["status"]),
            progress=int(row["progress"]),
            started_at=str(row["started_at"]),
            last_studied_at=str(row["last_studied_at"]),
            completed_at=(
                None if row["completed_at"] is None else str(row["completed_at"])
            ),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
            revision=int(row["revision"]),
            deleted_at=None if row["deleted_at"] is None else str(row["deleted_at"]),
            sync_status=str(row["sync_status"]),
        )

    def _new_uuid(self) -> str:
        value = str(self._uuid_factory())
        try:
            normalized = str(UUID(value))
        except (ValueError, AttributeError, TypeError) as exc:
            raise StudyRecordRepositoryError(
                "Generated local record identity is invalid"
            ) from exc
        if normalized != value:
            raise StudyRecordRepositoryError(
                "Generated local record identity is not canonical"
            )
        return value

    def _timestamp(self) -> str:
        value = self._now()
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()

    @staticmethod
    def _validate_profile_id(profile_id: str) -> str:
        try:
            normalized = str(UUID(profile_id))
        except (ValueError, AttributeError, TypeError) as exc:
            raise CorruptProfileError("Local study profile identity is invalid") from exc
        if normalized != profile_id:
            raise CorruptProfileError("Local study profile identity is not canonical")
        return profile_id
