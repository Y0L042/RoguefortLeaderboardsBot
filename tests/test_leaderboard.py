import datetime

import pytest

from config import Dungeon
from leaderboard import (
    BOARD_TYPES,
    DIVIDER,
    MAX_NAME_LENGTH,
    MAX_TEAM_NAME_LENGTH,
    Score,
    build_embeds,
    format_date,
    format_name,
    format_names,
    format_time,
    render_table,
)

SWIFTEST = BOARD_TYPES["swiftest"]
MASTERY = BOARD_TYPES["mastery"]
SOLO = Dungeon("monadic", "The Monadic Descent", 1, True, ["swiftest", "mastery"])


def make_score(**overrides) -> Score:
    fields = dict(
        names=("Hero",),
        level=10,
        danger_level=3,
        turns=1000,
        kills=50,
        time_seconds=300,
        score=10_000,
        haul=50_000,
        date=datetime.date(2026, 10, 29),
        victory=True,
    )
    fields.update(overrides)
    return Score(**fields)


def table_rows(table: str) -> list[str]:
    """The header and data lines of a rendered table, without dividers."""
    return [line for line in table.split("\n") if line != DIVIDER]


@pytest.mark.parametrize(
    ("seconds", "expected"), [(0, "0:00"), (59, "0:59"), (60, "1:00"), (3725, "62:05")]
)
def test_format_time(seconds, expected):
    assert format_time(seconds) == expected


def test_format_date():
    assert format_date(datetime.date(2026, 10, 29)) == "Oct 29"
    assert format_date(datetime.date(2026, 1, 5)) == "Jan 5"


def test_format_name_replaces_backticks():
    assert format_name("a`b`c") == "a'b'c"


def test_format_name_truncates_long_names():
    name = format_name("Y0L042 the Affable Wanderer")
    assert len(name) == MAX_NAME_LENGTH
    assert name.endswith("…")
    assert format_name("x" * MAX_NAME_LENGTH) == "x" * MAX_NAME_LENGTH


def test_format_names_solo_uses_solo_limit():
    assert len(format_names(("x" * 30,))) == MAX_NAME_LENGTH


def test_format_names_joins_and_truncates_teams():
    assert format_names(("Evan", "Hariel")) == "Evan, Hariel"
    team = format_names(("Evan", "Hariel", "Sen", "Fromager Colby"))
    assert team == "Evan, Hariel, Sen, From…"
    assert len(team) == MAX_TEAM_NAME_LENGTH


def test_swiftest_ranks_wins_first_then_fewest_turns():
    loss = make_score(names=("loss",), turns=10, victory=False)
    slow = make_score(names=("slow",), turns=900)
    fast = make_score(names=("fast",), turns=300)
    assert [row.names[0] for row in SWIFTEST.rank([loss, slow, fast])] == ["fast", "slow", "loss"]


def test_mastery_ranks_highest_score_first():
    rows = [make_score(names=(str(score),), score=score) for score in (5, 20, 10)]
    assert [row.names[0] for row in MASTERY.rank(rows)] == ["20", "10", "5"]


@pytest.mark.parametrize("board", BOARD_TYPES.values())
def test_boards_keep_top_ten(board):
    rows = [make_score(turns=i, score=i) for i in range(15)]
    assert len(board.rank(rows)) == 10
    assert len(board.rank(rows[:3])) == 3


@pytest.mark.parametrize("board", BOARD_TYPES.values())
def test_rows_are_aligned(board):
    rows = [
        make_score(names=("A",), turns=5, score=5, haul=1, kills=1),
        make_score(names=("Much Longer Name",), turns=12_345, score=99_999, haul=98_769, kills=729),
    ]
    lines = table_rows(render_table(rows, board.columns))
    # Strip the rank emoji; every row of cells must be the same width
    cell_lines = [line.split(" ", 1)[1] for line in lines]
    assert len({len(line) for line in cell_lines}) == 1
    # Numbers are right-aligned, names left-aligned
    assert "`A               `" in cell_lines[1]
    assert "`    1`" in cell_lines[1]  # kills


def test_medals_and_dividers():
    rows = [make_score(turns=i) for i in range(10)]
    lines = render_table(rows, SWIFTEST.columns).split("\n")
    assert lines[0].startswith("#️⃣")
    assert lines[1] == DIVIDER
    assert [line.split(" ")[0] for line in lines[2:5]] == ["🥇", "🥈", "🥉"]
    assert lines[5] == DIVIDER
    assert lines[6].startswith("4️⃣")
    assert lines[-1].startswith("🔟")


def test_number_formatting():
    row = make_score(turns=1_005, score=14_423, haul=98_769)
    swift = render_table([row], SWIFTEST.columns)
    master = render_table([row], MASTERY.columns)
    assert "1,005" in swift
    assert "14,423" in master
    assert "98,769g" in master
    assert "Oct 29" in swift and "Oct 29" in master


def test_build_embeds_follows_dungeon_boards():
    swift, master = build_embeds(SOLO, [make_score()])
    assert "Swiftest" in swift.title
    assert "Mastery" in master.title
    assert "Turns" in swift.description and "Score" not in swift.description
    assert "Score" in master.description and "Haul" in master.description
    # The dungeon label goes on the first embed, the footer on the last
    assert swift.author.name == "The Monadic Descent · 1 player"
    assert master.author.name is None
    assert swift.footer.text is None
    assert master.footer.text == "Updated"


def test_build_embeds_single_board():
    dungeon = Dungeon("dyadic", "The Dyadic Vault", 2, True, ["mastery"])
    (embed,) = build_embeds(dungeon, [make_score()])
    assert "Mastery" in embed.title
    assert embed.author.name == "The Dyadic Vault · 2 players"
    assert embed.footer.text == "Updated"


def test_build_embeds_with_no_scores():
    for embed in build_embeds(SOLO, []):
        assert "No runs yet" in embed.description


def test_message_fits_discord_limit():
    # Discord allows 6000 characters across all embeds of one message
    dungeon = Dungeon("tetradic", "The Tetradic Keep", 4, True, list(BOARD_TYPES))
    rows = [
        make_score(
            names=("W" * 32,) * 4,
            turns=99_999 + i,
            score=99_999 - i,
            haul=9_999_999,
            kills=9_999,
        )
        for i in range(15)
    ]
    assert sum(len(embed) for embed in build_embeds(dungeon, rows)) < 6000
