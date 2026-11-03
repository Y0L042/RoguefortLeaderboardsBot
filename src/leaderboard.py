"""Leaderboard data model and embed rendering. Pure: no Discord client, no env vars."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Callable, Final, Literal, NamedTuple

import discord

if TYPE_CHECKING:
    from config import Dungeon


class Score(NamedTuple):
    names: tuple[str, ...]  # one per party member
    level: int
    danger_level: int
    turns: int
    kills: int
    time_seconds: int
    score: int  # mastery score
    haul: int  # gold
    date: datetime.date
    victory: bool


class Column(NamedTuple):
    header: str
    format: Callable[[Score], str]
    align: Literal["<", ">"] = ">"


class BoardType(NamedTuple):
    title: str
    subtitle: str
    columns: list[Column]
    rank: Callable[[list[Score]], list[Score]]  # sort and keep the top TOP_N


MEDALS: Final[list[str]] = ["🥇", "🥈", "🥉"]
RANK_EMOJI: Final[list[str]] = ["4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
DIVIDER: Final[str] = "━━━━━━━━━━━━━━━━━━━━━━"
TOP_N: Final[int] = 10
MAX_NAME_LENGTH: Final[int] = 16
MAX_TEAM_NAME_LENGTH: Final[int] = 24
COLOUR: Final[int] = 0xF1C40F


def format_time(total_seconds: int) -> str:
    """Format seconds as m:ss."""
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}:{seconds:02}"


def format_date(date: datetime.date) -> str:
    """Format a date as e.g. 'Oct 29'."""
    return f"{date:%b} {date.day}"


def format_name(name: str, max_length: int = MAX_NAME_LENGTH) -> str:
    """Make a name safe for a code span and short enough not to wrap on mobile."""
    name = name.replace("`", "'")
    if len(name) > max_length:
        name = name[: max_length - 1] + "…"
    return name


def format_names(names: tuple[str, ...]) -> str:
    """Join a party's names; teams get a wider cell than solo players."""
    max_length = MAX_NAME_LENGTH if len(names) == 1 else MAX_TEAM_NAME_LENGTH
    return format_name(", ".join(names), max_length)


PLAYER_COLUMN: Final[Column] = Column("Player", lambda row: format_names(row.names), "<")

BOARD_TYPES: Final[dict[str, BoardType]] = {
    "swiftest": BoardType(
        title="⚡ Swiftest",
        subtitle="Wins first, fewest turns on top",
        columns=[
            PLAYER_COLUMN,
            Column("Lvl", lambda row: str(row.level)),
            Column("Danger", lambda row: str(row.danger_level)),
            Column("Turns", lambda row: f"{row.turns:,}"),
            Column("Kills", lambda row: f"{row.kills:,}"),
            Column("Time", lambda row: format_time(row.time_seconds)),
            Column("Date", lambda row: format_date(row.date)),
        ],
        rank=lambda scores: sorted(scores, key=lambda row: (not row.victory, row.turns))[:TOP_N],
    ),
    "mastery": BoardType(
        title="🏆 Mastery",
        subtitle="Floors, kills, treasure and damage avoided",
        columns=[
            PLAYER_COLUMN,
            Column("Lvl", lambda row: str(row.level)),
            Column("Danger", lambda row: str(row.danger_level)),
            Column("Score", lambda row: f"{row.score:,}"),
            Column("Kills", lambda row: f"{row.kills:,}"),
            Column("Haul", lambda row: f"{row.haul:,}g"),
            Column("Date", lambda row: format_date(row.date)),
        ],
        rank=lambda scores: sorted(scores, key=lambda row: -row.score)[:TOP_N],
    ),
}


def render_table(rows: list[Score], columns: list[Column]) -> str:
    """Render ranked rows as aligned code-span cells, with a header and medal dividers."""
    cells = [[column.header for column in columns]] + [
        [column.format(row) for column in columns] for row in rows
    ]
    widths = [max(len(line[c]) for line in cells) for c in range(len(columns))]

    def format_row(r: int) -> str:
        return " ".join(
            f"`{cells[r][c]:{column.align}{widths[c]}}`" for c, column in enumerate(columns)
        )

    lines = [f"#️⃣ {format_row(0)}", DIVIDER]
    for i in range(len(rows)):
        rank = MEDALS[i] if i < 3 else RANK_EMOJI[i - 3]
        if i == 3:
            lines.append(DIVIDER)
        lines.append(f"{rank} {format_row(i + 1)}")
    return "\n".join(lines)


def build_board(board: BoardType, scores: list[Score]) -> discord.Embed:
    rows = board.rank(scores)
    table = render_table(rows, board.columns) if rows else "*No runs yet*"
    return discord.Embed(
        title=board.title,
        description=f"*{board.subtitle}*\n{DIVIDER}\n{table}",
        colour=COLOUR,
    )


def dungeon_label(dungeon: Dungeon) -> str:
    """The first embed's author; also how the bot finds a dungeon's message again."""
    return f"{dungeon.name} · {dungeon.players} player{'s' if dungeon.players > 1 else ''}"


def build_embeds(dungeon: Dungeon, scores: list[Score]) -> list[discord.Embed]:
    """Build one embed per enabled board of the dungeon, in config order."""
    embeds = [build_board(BOARD_TYPES[board], scores) for board in dungeon.boards]
    embeds[0].set_author(name=dungeon_label(dungeon))
    embeds[-1].set_footer(text="Updated")
    embeds[-1].timestamp = discord.utils.utcnow()
    return embeds
