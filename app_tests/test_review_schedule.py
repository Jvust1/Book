from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from app.study.repository import StudyRecordRepository
from app.study.review_schedule import ReviewScheduleRepository, ReviewScheduleService
from runtime.review_scheduler import FSRSReviewScheduler


class FakeBookService:
    class Item:
        def __init__(self, source_id):
            self.source_id = source_id

    class Mode:
        def __init__(self):
            self.items = [FakeBookService.Item("def_1"), FakeBookService.Item("thm_1")]

    def mode(self, course_id, section_id, mode):
        assert course_id == "course"
        assert section_id == "s1"
        assert mode == "review"
        return self.Mode()


class FakeRating:
    Again = 1
    Hard = 2
    Good = 3
    Easy = 4


class FakeCard:
    def __init__(self, payload=None):
        self.payload = dict(payload or {"due": "now", "reviews": 0})

    @classmethod
    def from_dict(cls, payload):
        return cls(payload)

    def to_dict(self):
        return dict(self.payload)


class FakeLog:
    def __init__(self, rating):
        self.rating = rating

    def to_dict(self):
        return {"rating": self.rating}


class FakeScheduler:
    def review_card(self, *, card, rating, **_kwargs):
        value = dict(card.payload)
        value["reviews"] = int(value.get("reviews", 0)) + 1
        value["due"] = "2026-10-05T00:00:00+00:00"
        return FakeCard(value), FakeLog(rating)


class ReviewScheduleServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        db = Path(self.tmp.name) / "study.sqlite3"
        StudyRecordRepository(db)
        repository = ReviewScheduleRepository(db)
        scheduler = FSRSReviewScheduler(FakeScheduler(), FakeCard, FakeRating)
        self.service = ReviewScheduleService(FakeBookService(), repository, scheduler)

    def test_review_persists_card_between_calls(self):
        first = self.service.review("course", "s1", "def_1", "good")
        second = self.service.review("course", "s1", "def_1", "easy")
        self.assertEqual(first.card["reviews"], 1)
        self.assertEqual(second.card["reviews"], 2)
        self.assertEqual(second.due, "2026-10-05T00:00:00+00:00")

    def test_non_review_source_is_rejected(self):
        from app.api.errors import AppNotFoundError
        with self.assertRaises(AppNotFoundError):
            self.service.review("course", "s1", "remark_1", "good")


if __name__ == "__main__":
    unittest.main()
