"""Where leaderboard scores come from.

Each data source is a ScoreSource. To add a real one (HTTP API, database, JSON export),
write a class with an async fetch(), map the raw records with parse_score(), and
register it in SOURCES. Nothing else needs to change.
"""

import datetime
import os
from typing import Any, Protocol

from config import Dungeon
from leaderboard import Score


class ScoreSource(Protocol):
    async def fetch(self, dungeon: Dungeon) -> list[Score]:
        """Return the dungeon's runs, in any order."""
        ...


def parse_score(raw: dict[str, Any]) -> Score:
    """Map one raw record (e.g. from JSON or a DB row) to a Score."""
    return Score(
        names=tuple(str(name) for name in raw["names"]),
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


MOCK_NAMES = [
    "Merlinus", "xXFireballXx", "Zaltharion", "PotionSeller", "Grimbeard",
    "Hexorcist", "Gandalfo", "ManaPotato", "Rincewand", "NoobSlayer99",
]


class MockSource:
    """Fake data that changes on every fetch, so refreshes are visible."""

    def __init__(self) -> None:
        self.x = 7

    async def fetch(self, dungeon: Dungeon) -> list[Score]:
        self.x += 1
        x = self.x

        def party(i: int) -> tuple[str, ...]:
            return tuple(MOCK_NAMES[(i + j) % len(MOCK_NAMES)] for j in range(dungeon.players))

        def day(i: int) -> datetime.date:
            return datetime.date(2026, 10, 1 + i)

        return [
            Score(party(0), 12, 5, 7765, 87, 754 + x, 14_423, 98_769, day(0), True),
            Score(party(1), 11, 5, 6418, 79, 790 + x * 2, 13_906, 84_071, day(1), True),
            Score(party(2), 10, 4, 5937, 64, 812 + x * 10, 13_676, 72_183, day(2), True),
            Score(party(3), 9, 4, 4203, 51, 905 + x * 100, 13_238, 71_860, day(3), True),
            Score(party(4), 8, 3, 3856, 42, 1010 + x * 5, 12_698, 64_459, day(4), True),
            Score(party(5), 8, 3, 2391, 38, 1102, 12_482, 53_786, day(5), False),
            Score(party(6), 7, 3, 1074, 33, 1187, 12_460, 55_196, day(6), True),
            Score(party(7), 6, 2, 619, 27, 1240, 12_384, 57_390, day(7), False),
            Score(party(8), 5, 2, 582, 19, 1325, 12_232, 54_344, day(8), True),
            Score(party(9), 4, 1, 347, 12, 1410, 12_226, 54_305, day(9), False),
        ]


SOURCES: dict[str, type[ScoreSource]] = {
    "mock": MockSource,
}

_source: ScoreSource | None = None


async def fetch_scores(dungeon: Dungeon) -> list[Score]:
    """Fetch a dungeon's scores from the source named by SCORE_SOURCE (default: mock)."""
    global _source
    if _source is None:
        _source = SOURCES[os.environ.get("SCORE_SOURCE", "mock")]()
    return await _source.fetch(dungeon)
