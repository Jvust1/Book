"""Optional FSRS spaced-repetition scheduling boundary for Book.

Upstream: open-spaced-repetition/py-fsrs @
9446cb06605c597a063aeee49f7d188d42e34dc2 (MIT).

Book remains authoritative for learning content and source provenance. FSRS is
used only to schedule when a source-backed review item should be shown again.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping


_RATING_NAMES = {
    "again": "Again",
    "hard": "Hard",
    "good": "Good",
    "easy": "Easy",
}


@dataclass(frozen=True)
class ScheduledReview:
    card: dict[str, Any]
    review_log: dict[str, Any]

    @property
    def due(self) -> Any:
        return self.card.get("due")


class FSRSReviewScheduler:
    """Adapter around py-fsrs Card/Rating/Scheduler serialization contracts."""

    def __init__(self, scheduler: Any, card_type: Any, rating_type: Any) -> None:
        if not callable(getattr(scheduler, "review_card", None)):
            raise TypeError("scheduler must provide review_card()")
        if not callable(getattr(card_type, "from_dict", None)):
            raise TypeError("card_type must provide from_dict()")
        self._scheduler = scheduler
        self._card_type = card_type
        self._rating_type = rating_type

    def new_card(self) -> dict[str, Any]:
        card = self._card_type()
        to_dict = getattr(card, "to_dict", None)
        if not callable(to_dict):
            raise TypeError("FSRS Card must provide to_dict()")
        return dict(to_dict())

    def review(
        self,
        card_state: Mapping[str, Any],
        rating: str,
        *,
        review_datetime: datetime | None = None,
    ) -> ScheduledReview:
        normalized = str(rating).strip().casefold()
        member_name = _RATING_NAMES.get(normalized)
        if member_name is None:
            raise ValueError("rating must be one of: again, hard, good, easy")
        try:
            rating_value = getattr(self._rating_type, member_name)
        except AttributeError as exc:
            raise TypeError(f"rating_type missing {member_name}") from exc

        card = self._card_type.from_dict(dict(card_state))
        kwargs: dict[str, Any] = {"card": card, "rating": rating_value}
        if review_datetime is not None:
            kwargs["review_datetime"] = review_datetime
        next_card, log = self._scheduler.review_card(**kwargs)

        card_to_dict = getattr(next_card, "to_dict", None)
        log_to_dict = getattr(log, "to_dict", None)
        if not callable(card_to_dict) or not callable(log_to_dict):
            raise TypeError("FSRS review_card() result must provide to_dict()")
        return ScheduledReview(
            card=dict(card_to_dict()),
            review_log=dict(log_to_dict()),
        )


def create_fsrs_review_scheduler(**scheduler_kwargs: Any) -> FSRSReviewScheduler:
    """Create py-fsrs lazily so Book core has no hard dependency on it."""
    try:
        from fsrs import Card, Rating, Scheduler
    except ImportError as exc:
        raise RuntimeError(
            "py-fsrs is optional; install package 'fsrs' before enabling adaptive review scheduling"
        ) from exc
    return FSRSReviewScheduler(
        Scheduler(**scheduler_kwargs),
        Card,
        Rating,
    )
