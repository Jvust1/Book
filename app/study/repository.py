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
        return self._validate_profile_id(str(row[0]))

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
                    self._validate_profile_id(str(row[0]))
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
        return sqlite3.connect(self._db_path, isolation_level=None)

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
