"""Load the refresh interval, dungeons and their enabled boards from config.toml."""

import sys
from pathlib import Path
from typing import Final, NamedTuple

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from leaderboard import BOARD_TYPES

CONFIG_PATH: Final[Path] = Path(__file__).resolve().parent.parent / "config.toml"
DEFAULT_REFRESH_SECONDS: Final[int] = 60
MIN_REFRESH_SECONDS: Final[int] = 10  # stay well clear of Discord's rate limits


class ConfigError(ValueError):
    pass


class Dungeon(NamedTuple):
    id: str
    name: str
    players: int
    enabled: bool
    boards: list[str]  # enabled board types, in file order

    @property
    def visible(self) -> bool:
        """Whether the dungeon gets a message: enabled, with at least one board."""
        return self.enabled and bool(self.boards)


class Config(NamedTuple):
    refresh_seconds: int
    dungeons: list[Dungeon]


def load_config(path: Path = CONFIG_PATH) -> Config:
    """Parse and validate the config. Raises ConfigError on a bad entry."""
    with open(path, "rb") as file:
        data = tomllib.load(file)

    refresh_seconds = data.get("refresh_seconds", DEFAULT_REFRESH_SECONDS)
    if not isinstance(refresh_seconds, int) or refresh_seconds < MIN_REFRESH_SECONDS:
        raise ConfigError(f"'refresh_seconds' must be at least {MIN_REFRESH_SECONDS}")

    dungeons = []
    for dungeon_id, entry in data.get("dungeons", {}).items():
        if "name" not in entry:
            raise ConfigError(f"dungeon {dungeon_id!r}: missing 'name'")
        players = entry.get("players", 1)
        if not isinstance(players, int) or players < 1:
            raise ConfigError(f"dungeon {dungeon_id!r}: 'players' must be at least 1")
        boards = entry.get("boards", {})
        for board in boards:
            if board not in BOARD_TYPES:
                raise ConfigError(
                    f"dungeon {dungeon_id!r}: unknown board {board!r}, "
                    f"expected one of {', '.join(BOARD_TYPES)}"
                )
        dungeons.append(
            Dungeon(
                id=dungeon_id,
                name=entry["name"],
                players=players,
                enabled=bool(entry.get("enabled", True)),
                boards=[board for board, on in boards.items() if on],
            )
        )
    return Config(refresh_seconds, dungeons)
