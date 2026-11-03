"""Leaderboard data model and embed rendering. Pure: no Discord client, no env vars."""

import datetime
from typing import Callable, Final, Literal, NamedTuple

import discord


class Score(NamedTuple):
    name: str
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


MEDALS: Final[list[str]] = ["🥇", "🥈", "🥉"]
RANK_EMOJI: Final[list[str]] = ["4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
DIVIDER: Final[str] = "━━━━━━━━━━━━━━━━━━━━━━"
TOP_N: Final[int] = 10
MAX_NAME_LENGTH: Final[int] = 16
COLOUR: Final[int] = 0xF1C40F


def format_time(total_seconds: int) -> str:
    """Format seconds as m:ss."""
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}:{seconds:02}"


def format_date(date: datetime.date) -> str:
    """Format a date as e.g. 'Oct 29'."""
    return f"{date:%b} {date.day}"


def format_name(name: str) -> str:
    """Make a name safe for a code span and short enough not to wrap on mobile."""
    name = name.replace("`", "'")
    if len(name) > MAX_NAME_LENGTH:
        name = name[: MAX_NAME_LENGTH - 1] + "…"
    return name


SWIFTEST_COLUMNS: Final[list[Column]] = [
    Column("Player", lambda row: format_name(row.name), "<"),
    Column("Lvl", lambda row: str(row.level)),
    Column("Danger", lambda row: str(row.danger_level)),
    Column("Turns", lambda row: f"{row.turns:,}"),
    Column("Kills", lambda row: f"{row.kills:,}"),
    Column("Time", lambda row: format_time(row.time_seconds)),
    Column("Date", lambda row: format_date(row.date)),
]

MASTERY_COLUMNS: Final[list[Column]] = [
    Column("Player", lambda row: format_name(row.name), "<"),
    Column("Lvl", lambda row: str(row.level)),
    Column("Danger", lambda row: str(row.danger_level)),
    Column("Score", lambda row: f"{row.score:,}"),
    Column("Kills", lambda row: f"{row.kills:,}"),
    Column("Haul", lambda row: f"{row.haul:,}g"),
    Column("Date", lambda row: format_date(row.date)),
]


def swiftest(scores: list[Score]) -> list[Score]:
    """Top runs: wins first, then fewest turns."""
    return sorted(scores, key=lambda row: (not row.victory, row.turns))[:TOP_N]


def mastery(scores: list[Score]) -> list[Score]:
    """Top runs by highest mastery score."""
    return sorted(scores, key=lambda row: -row.score)[:TOP_N]


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


def build_board(title: str, subtitle: str, rows: list[Score], columns: list[Column]) -> discord.Embed:
    table = render_table(rows, columns) if rows else "*No runs yet*"
    return discord.Embed(
        title=title,
        description=f"*{subtitle}*\n{DIVIDER}\n{table}",
        colour=COLOUR,
    )


def build_embeds(scores: list[Score]) -> list[discord.Embed]:
    """Build the Swiftest and Mastery embeds, in that order."""
    embeds = [
        build_board(
            "⚡ Swiftest ⚡", "Wins first, fewest turns on top", swiftest(scores), SWIFTEST_COLUMNS
        ),
        build_board(
            "🏆 Mastery 🏆",
            "Floors, kills, treasure and damage avoided",
            mastery(scores),
            MASTERY_COLUMNS,
        ),
    ]
    embeds[-1].set_footer(text="Updated")
    embeds[-1].timestamp = discord.utils.utcnow()
    return embeds
