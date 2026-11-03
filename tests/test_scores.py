import datetime

import pytest

from leaderboard import Score
from scores import MockSource, parse_score


async def test_mock_source_returns_scores():
    scores = await MockSource().fetch()
    assert scores
    assert all(isinstance(row, Score) for row in scores)


async def test_mock_source_changes_between_fetches():
    source = MockSource()
    assert await source.fetch() != await source.fetch()


def test_parse_score():
    raw = {
        "name": "Evan",
        "level": "100",
        "danger_level": 8,
        "turns": 6628,
        "kills": 729,
        "time_seconds": 354,
        "score": 14423,
        "haul": 98769,
        "date": "2026-10-23",
        "victory": True,
    }
    assert parse_score(raw) == Score(
        "Evan", 100, 8, 6628, 729, 354, 14423, 98769, datetime.date(2026, 10, 23), True
    )


def test_parse_score_missing_field():
    with pytest.raises(KeyError):
        parse_score({"name": "Evan"})
