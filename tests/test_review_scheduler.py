from __future__ import annotations

import unittest
from datetime import datetime, timezone

from runtime.review_scheduler import FSRSReviewScheduler


class FakeRating:
    Again = 1
    Hard = 2
    Good = 3
    Easy = 4


class FakeCard:
    def __init__(self, payload=None):
        self.payload = dict(payload or {"due": "now", "state": "new"})

    @classmethod
    def from_dict(cls, payload):
        return cls(payload)

    def to_dict(self):
        return dict(self.payload)


class FakeLog:
    def __init__(self, rating):
        self.rating = rating

    def to_dict(self):
        return {"rating": self.rating, "review_datetime": "2026-09-30T15:00:00+00:00"}


class FakeScheduler:
    def __init__(self):
        self.calls = []

    def review_card(self, **kwargs):
        self.calls.append(kwargs)
        card = kwargs["card"]
        next_payload = dict(card.payload)
        next_payload["due"] = "2026-10-03T15:00:00+00:00"
        next_payload["state"] = "review"
        return FakeCard(next_payload), FakeLog(kwargs["rating"])


class FSRSReviewSchedulerTests(unittest.TestCase):
    def setUp(self):
        self.upstream = FakeScheduler()
        self.scheduler = FSRSReviewScheduler(self.upstream, FakeCard, FakeRating)

    def test_new_card_is_serializable(self):
        self.assertEqual(
            self.scheduler.new_card(),
            {"due": "now", "state": "new"},
        )

    def test_good_review_returns_next_serialized_card_and_log(self):
        when = datetime(2026, 9, 30, 15, 0, tzinfo=timezone.utc)
        result = self.scheduler.review(
            {"due": "now", "state": "new"},
            "good",
            review_datetime=when,
        )
        self.assertEqual(result.card["state"], "review")
        self.assertEqual(result.due, "2026-10-03T15:00:00+00:00")
        self.assertEqual(result.review_log["rating"], FakeRating.Good)
        self.assertEqual(self.upstream.calls[0]["review_datetime"], when)

    def test_all_ratings_map_to_upstream_enum(self):
        expected = {
            "again": FakeRating.Again,
            "hard": FakeRating.Hard,
            "good": FakeRating.Good,
            "easy": FakeRating.Easy,
        }
        for name, value in expected.items():
            with self.subTest(name=name):
                self.scheduler.review({"due": "now"}, name)
                self.assertEqual(self.upstream.calls[-1]["rating"], value)

    def test_invalid_rating_fails_closed(self):
        with self.assertRaises(ValueError):
            self.scheduler.review({"due": "now"}, "perfect")


if __name__ == "__main__":
    unittest.main()
