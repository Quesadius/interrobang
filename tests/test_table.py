"""Tests for the Table component."""

from interrobang import KeyMsg, KeyType
from interrobang.components import Column, Table
from interrobang.testing import strip_ansi


def make():
    return Table(
        columns=[Column("Name", 14), Column("Mark", 6)],
        rows=[["Interrobang", "‽"], ["Exclaim", "!"], ["Question", "?"]],
        height=8,
    )


def press(t, key_type, runes=""):
    return t.update(KeyMsg(key_type, runes))[0]


class TestNavigation:
    def test_down(self):
        t = press(make(), KeyType.DOWN)
        assert t.cursor == 1
        assert t.selected_row() == ["Exclaim", "!"]

    def test_up_clamps(self):
        assert press(make(), KeyType.UP).cursor == 0

    def test_down_clamps(self):
        t = make()
        for _ in range(10):
            t = press(t, KeyType.DOWN)
        assert t.cursor == 2

    def test_goto_top_bottom(self):
        t = make()
        t = press(t, KeyType.END)
        assert t.cursor == 2
        t = press(t, KeyType.HOME)
        assert t.cursor == 0

    def test_unfocused_ignores_keys(self):
        t = make()
        t.focused = False
        t = press(t, KeyType.DOWN)
        assert t.cursor == 0


class TestSelection:
    def test_selected_row(self):
        assert make().selected_row() == ["Interrobang", "‽"]

    def test_empty(self):
        assert Table(columns=[Column("A", 4)], rows=[]).selected_row() is None


class TestView:
    def test_header_and_underline(self):
        lines = strip_ansi(make().view()).split("\n")
        assert "Name" in lines[0]
        assert "Mark" in lines[0]
        assert set(lines[1]) == {"─"}

    def test_rows_present(self):
        view = strip_ansi(make().view())
        assert "Interrobang" in view
        assert "Question" in view

    def test_truncates_long_cells(self):
        t = Table(columns=[Column("X", 4)], rows=[["abcdefgh"]], height=5)
        view = strip_ansi(t.view())
        assert "abcdefgh" not in view
        assert "abcd" in view

    def test_set_rows_resets(self):
        t = make()
        t = press(t, KeyType.DOWN)
        t.set_rows([["a", "b"]])
        assert t.cursor == 0
