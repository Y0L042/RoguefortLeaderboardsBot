import datetime

import pytest

from leaderboard import (
    DIVIDER,
    MASTERY_COLUMNS,
    MAX_NAME_LENGTH,
    SWIFTEST_COLUMNS,
    Score,
    build_embeds,
    format_date,
    format_name,
    format_time,
    mastery,
    render_table,
    swiftest,
)


def make_score(**overrides) -> Score:
    fields = dict(
        name="Hero",
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


def test_swiftest_ranks_wins_first_then_fewest_turns():
    loss = make_score(name="loss", turns=10, victory=False)
    slow = make_score(name="slow", turns=900)
    fast = make_score(name="fast", turns=300)
    assert [row.name for row in swiftest([loss, slow, fast])] == ["fast", "slow", "loss"]


def test_mastery_ranks_highest_score_first():
    rows = [make_score(name=str(score), score=score) for score in (5, 20, 10)]
    assert [row.name for row in mastery(rows)] == ["20", "10", "5"]


@pytest.mark.parametrize("board", [swiftest, mastery])
def test_boards_keep_top_ten(board):
    rows = [make_score(turns=i, score=i) for i in range(15)]
    assert len(board(rows)) == 10
    assert len(board(rows[:3])) == 3


@pytest.mark.parametrize("columns", [SWIFTEST_COLUMNS, MASTERY_COLUMNS])
def test_rows_are_aligned(columns):
    rows = [
        make_score(name="A", turns=5, score=5, haul=1, kills=1),
        make_score(name="Much Longer Name", turns=12_345, score=99_999, haul=98_769, kills=729),
    ]
    lines = table_rows(render_table(rows, columns))
    # Strip the rank emoji; every row of cells must be the same width
    cell_lines = [line.split(" ", 1)[1] for line in lines]
    assert len({len(line) for line in cell_lines}) == 1
    # Numbers are right-aligned, names left-aligned
    assert "`A               `" in cell_lines[1]
    assert "`    1`" in cell_lines[1]  # kills


def test_medals_and_dividers():
    rows = [make_score(turns=i) for i in range(10)]
    lines = render_table(rows, SWIFTEST_COLUMNS).split("\n")
    assert lines[0].startswith("#️⃣")
    assert lines[1] == DIVIDER
    assert [line.split(" ")[0] for line in lines[2:5]] == ["🥇", "🥈", "🥉"]
    assert lines[5] == DIVIDER
    assert lines[6].startswith("4️⃣")
    assert lines[-1].startswith("🔟")


def test_number_formatting():
    row = make_score(turns=1_005, score=14_423, haul=98_769)
    swift = render_table([row], SWIFTEST_COLUMNS)
    master = render_table([row], MASTERY_COLUMNS)
    assert "1,005" in swift
    assert "14,423" in master
    assert "98,769g" in master
    assert "Oct 29" in swift and "Oct 29" in master


def test_build_embeds_returns_swiftest_then_mastery():
    swift, master = build_embeds([make_score()])
    assert "Swiftest" in swift.title
    assert "Mastery" in master.title
    assert "Turns" in swift.description and "Score" not in swift.description
    assert "Score" in master.description and "Haul" in master.description
    # Only the last embed carries the footer
    assert swift.footer.text is None
    assert master.footer.text == "Updated"


def test_build_embeds_with_no_scores():
    for embed in build_embeds([]):
        assert "No runs yet" in embed.description


def test_message_fits_discord_limit():
    # Discord allows 6000 characters across all embeds of one message
    rows = [
        make_score(name="W" * 32, turns=99_999 + i, score=99_999 - i, haul=9_999_999, kills=9_999)
        for i in range(15)
    ]
    assert sum(len(embed) for embed in build_embeds(rows)) < 6000
