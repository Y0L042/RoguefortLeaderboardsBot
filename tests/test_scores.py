import datetime

import pytest

from config import Dungeon
from leaderboard import Score
from scores import MockSource, parse_score


@pytest.mark.parametrize("players", [1, 2, 4])
async def test_mock_source_parties_match_dungeon(players):
    dungeon = Dungeon("d", "D", players, True, ["swiftest"])
    scores = await MockSource().fetch(dungeon)
    assert scores
    assert all(isinstance(row, Score) for row in scores)
    assert all(len(row.names) == players for row in scores)


async def test_mock_source_changes_between_fetches():
    dungeon = Dungeon("d", "D", 1, True, ["swiftest"])
    source = MockSource()
    assert await source.fetch(dungeon) != await source.fetch(dungeon)


def test_parse_score():
    raw = {
        "names": ["Evan", "Hariel"],
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
        ("Evan", "Hariel"), 100, 8, 6628, 729, 354, 14423, 98769, datetime.date(2026, 10, 23), True
    )


def test_parse_score_missing_field():
    with pytest.raises(KeyError):
        parse_score({"names": ["Evan"]})
