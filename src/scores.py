"""Where leaderboard scores come from.

Each data source is a ScoreSource. To add a real one (HTTP API, database, JSON export),
write a class with an async fetch(), map the raw records with parse_score(), and
register it in SOURCES. Nothing else needs to change.
"""

import datetime
import os
from typing import Any, Protocol

from leaderboard import Score


class ScoreSource(Protocol):
    async def fetch(self) -> list[Score]:
        """Return player scores, in any order."""
        ...


def parse_score(raw: dict[str, Any]) -> Score:
    """Map one raw record (e.g. from JSON or a DB row) to a Score."""
    return Score(
        name=str(raw["name"]),
        level=int(raw["level"]),
        danger_level=int(raw["danger_level"]),
        turns=int(raw["turns"]),
        kills=int(raw["kills"]),
        time_seconds=int(raw["time_seconds"]),
        score=int(raw["score"]),
        haul=int(raw["haul"]),
        date=datetime.date.fromisoformat(raw["date"]),
        victory=bool(raw["victory"]),
    )


class MockSource:
    """Fake data that changes on every fetch, so refreshes are visible."""

    def __init__(self) -> None:
        self.x = 7

    async def fetch(self) -> list[Score]:
        self.x += 1
        x = self.x
        day = datetime.date(2026, 10, 1)
        return [
            Score("Merlinus", 12, 5, 7765, 87, 754 + x, 14_423, 98_769, day, True),
            Score("xXFireballXx", 11, 5, 6418, 79, 790 + x * 2, 13_906, 84_071, day, True),
            Score("Zaltharion", 10, 4, 5937, 64, 812 + x * 10, 13_676, 72_183, day, True),
            Score("PotionSeller", 9, 4, 4203, 51, 905 + x * 100, 13_238, 71_860, day, True),
            Score("Grimbeard", 8, 3, 3856, 42, 1010 + x * 5, 12_698, 64_459, day, True),
            Score("Hexorcist", 8, 3, 2391, 38, 1102, 12_482, 53_786, day, False),
            Score("Gandalfo", 7, 3, 1074, 33, 1187, 12_460, 55_196, day, True),
            Score("ManaPotato", 6, 2, 619, 27, 1240, 12_384, 57_390, day, False),
            Score("Rincewand", 5, 2, 582, 19, 1325, 12_232, 54_344, day, True),
            Score("NoobSlayer99", 4, 1, 347, 12, 1410, 12_226, 54_305, day, False),
        ]


SOURCES: dict[str, type[ScoreSource]] = {
    "mock": MockSource,
}

_source: ScoreSource | None = None


async def fetch_scores() -> list[Score]:
    """Fetch scores from the source named by SCORE_SOURCE (default: mock)."""
    global _source
    if _source is None:
        _source = SOURCES[os.environ.get("SCORE_SOURCE", "mock")]()
    return await _source.fetch()
