import pytest

from config import CONFIG_PATH, DEFAULT_REFRESH_SECONDS, ConfigError, Dungeon, load_config


def write_config(tmp_path, text: str):
    path = tmp_path / "config.toml"
    path.write_text(text, encoding="utf-8")
    return path


def test_real_config_loads():
    config = load_config(CONFIG_PATH)
    assert config.refresh_seconds >= 10
    dungeons = {dungeon.id: dungeon for dungeon in config.dungeons}
    assert list(dungeons) == ["monadic", "dyadic", "triadic", "tetradic", "infinite"]
    assert dungeons["monadic"].visible
    assert [dungeon.players for dungeon in dungeons.values()] == [1, 2, 3, 4, 1]
    assert not dungeons["infinite"].visible


def test_board_toggles_keep_order(tmp_path):
    path = write_config(
        tmp_path,
        """
        [dungeons.a]
        name = "A"
        boards = { mastery = true, swiftest = false }
        [dungeons.b]
        name = "B"
        boards = { mastery = true, swiftest = true }
        """,
    )
    a, b = load_config(path).dungeons
    assert a == Dungeon("a", "A", 1, True, ["mastery"])
    assert b.boards == ["mastery", "swiftest"]


def test_disabled_dungeon_is_not_visible(tmp_path):
    path = write_config(
        tmp_path,
        """
        [dungeons.a]
        name = "A"
        enabled = false
        boards = { swiftest = true }
        [dungeons.b]
        name = "B"
        boards = { swiftest = false }
        """,
    )
    a, b = load_config(path).dungeons
    assert not a.visible
    assert not b.visible  # enabled, but every board is off


@pytest.mark.parametrize(
    ("entry", "message"),
    [
        ('name = "A"\nboards = { fastest = true }', "unknown board 'fastest'"),
        ("boards = { swiftest = true }", "missing 'name'"),
        ('name = "A"\nplayers = 0', "'players' must be at least 1"),
    ],
)
def test_invalid_config(tmp_path, entry, message):
    path = write_config(tmp_path, f"[dungeons.a]\n{entry}\n")
    with pytest.raises(ConfigError, match=message):
        load_config(path)


def test_refresh_seconds(tmp_path):
    assert load_config(write_config(tmp_path, "refresh_seconds = 30")).refresh_seconds == 30
    assert load_config(write_config(tmp_path, "")).refresh_seconds == DEFAULT_REFRESH_SECONDS


@pytest.mark.parametrize("value", ["5", "0", "-60", '"60"', "1.5"])
def test_invalid_refresh_seconds(tmp_path, value):
    path = write_config(tmp_path, f"refresh_seconds = {value}")
    with pytest.raises(ConfigError, match="'refresh_seconds' must be at least 10"):
        load_config(path)
