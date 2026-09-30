from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from app.api.errors import AppNotFoundError, AppUnavailableError
from app.api.service import BookAppService
from runtime.review_scheduler import FSRSReviewScheduler, create_fsrs_review_scheduler


@dataclass(frozen=True)
class ReviewSchedule:
    course_id: str
    section_id: str
    source_id: str
    due: str | None
    card: dict[str, Any]
    review_log: dict[str, Any]


class ReviewScheduleRepository:
    """Persist FSRS card state beside the existing local StudyRecord database."""

    def __init__(self, db_path: Path, *, now: Callable[[], datetime] | None = None) -> None:
        self._db_path = Path(db_path)
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._db_path, isolation_level=None)
        connection.row_factory = sqlite3.Row
        return connection

    def _profile_id(self, connection: sqlite3.Connection) -> str:
        row = connection.execute(
            "SELECT profile_id FROM app_profile WHERE singleton = 1"
        ).fetchone()
        if row is None:
            raise RuntimeError("local study profile missing")
        return str(row["profile_id"])

    def _initialize(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = self._connect()
        try:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS review_schedules (
                    profile_id TEXT NOT NULL,
                    course_id TEXT NOT NULL,
                    section_id TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    card_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (profile_id, course_id, section_id, source_id)
                )
                """
            )
        finally:
            connection.close()

    def load(self, course_id: str, section_id: str, source_id: str) -> dict[str, Any] | None:
        connection = self._connect()
        try:
            profile_id = self._profile_id(connection)
            row = connection.execute(
                """
                SELECT card_json FROM review_schedules
                WHERE profile_id = ? AND course_id = ? AND section_id = ? AND source_id = ?
                """,
                (profile_id, course_id, section_id, source_id),
            ).fetchone()
        finally:
            connection.close()
        if row is None:
            return None
        value = json.loads(str(row["card_json"]))
        if not isinstance(value, dict):
            raise RuntimeError("stored FSRS card is invalid")
        return value

    def save(self, course_id: str, section_id: str, source_id: str, card: dict[str, Any]) -> None:
        encoded = json.dumps(card, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        timestamp = self._now().astimezone(timezone.utc).isoformat()
        connection = self._connect()
        try:
            profile_id = self._profile_id(connection)
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                INSERT INTO review_schedules (
                    profile_id, course_id, section_id, source_id, card_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(profile_id, course_id, section_id, source_id)
                DO UPDATE SET card_json = excluded.card_json, updated_at = excluded.updated_at
                """,
                (profile_id, course_id, section_id, source_id, encoded, timestamp),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()


class ReviewScheduleService:
    def __init__(
        self,
        book_service: BookAppService,
        repository: ReviewScheduleRepository,
        scheduler: FSRSReviewScheduler | None = None,
    ) -> None:
        self._book_service = book_service
        self._repository = repository
        self._scheduler = scheduler

    def _scheduler_or_raise(self) -> FSRSReviewScheduler:
        if self._scheduler is not None:
            return self._scheduler
        try:
            self._scheduler = create_fsrs_review_scheduler()
        except RuntimeError as exc:
            raise AppUnavailableError(
                code="review_scheduler_unavailable",
                user_message="自适应复习调度暂不可用",
                detail=str(exc),
            ) from exc
        return self._scheduler

    def review(
        self,
        course_id: str,
        section_id: str,
        source_id: str,
        rating: str,
    ) -> ReviewSchedule:
        review_mode = self._book_service.mode(course_id, section_id, "review")
        allowed = {item.source_id for item in review_mode.items}
        if source_id not in allowed:
            raise AppNotFoundError(
                code="review_item_not_found",
                user_message="复习条目不存在",
                detail=f"{source_id!r} is not a review item in section {section_id!r}",
            )

        scheduler = self._scheduler_or_raise()
        card = self._repository.load(course_id, section_id, source_id)
        if card is None:
            card = scheduler.new_card()
        result = scheduler.review(card, rating)
        self._repository.save(course_id, section_id, source_id, result.card)
        due = result.card.get("due")
        return ReviewSchedule(
            course_id=course_id,
            section_id=section_id,
            source_id=source_id,
            due=None if due is None else str(due),
            card=result.card,
            review_log=result.review_log,
        )
