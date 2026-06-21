"""Tests for the List component."""

from interrobang import KeyMsg, KeyType
from interrobang.components import Item, List
from interrobang.testing import strip_ansi


def make():
    items = [Item("Pocky", "snack"), Item("Ramen", "soup"), Item("Mochi", "dessert")]
    lst = List(items, width=30, height=14)
    lst.title = "Snacks"
    return lst


def press(lst, key_type, runes=""):
    return lst.update(KeyMsg(key_type, runes))[0]


class TestNavigation:
    def test_down(self):
        lst = press(make(), KeyType.DOWN)
        assert lst.cursor == 1
        assert lst.selected_item().title == "Ramen"

    def test_up_clamps(self):
        lst = press(make(), KeyType.UP)
        assert lst.cursor == 0

    def test_down_clamps_at_end(self):
        lst = make()
        for _ in range(10):
            lst = press(lst, KeyType.DOWN)
        assert lst.cursor == 2

    def test_vim_keys(self):
        lst = press(make(), KeyType.RUNES, "j")
        assert lst.cursor == 1

    def test_home_end(self):
        lst = make()
        lst = press(lst, KeyType.END)
        assert lst.cursor == 2
        lst = press(lst, KeyType.HOME)
        assert lst.cursor == 0


class TestSelection:
    def test_selected_item(self):
        assert make().selected_item().title == "Pocky"

    def test_empty_list(self):
        assert List([]).selected_item() is None


class TestFiltering:
    def test_filter_narrows(self):
        lst = make()
        lst = press(lst, KeyType.RUNES, "/")
        assert lst.filtering
        for ch in "mo":
            lst = press(lst, KeyType.RUNES, ch)
        assert [i.title for i in lst.visible_items()] == ["Mochi"]

    def test_filter_enter_confirms(self):
        lst = make()
        lst = press(lst, KeyType.RUNES, "/")
        lst = press(lst, KeyType.RUNES, "r")
        lst = press(lst, KeyType.ENTER)
        assert not lst.filtering
        assert lst.filter_text == "r"

    def test_filter_esc_clears(self):
        lst = make()
        lst = press(lst, KeyType.RUNES, "/")
        lst = press(lst, KeyType.RUNES, "r")
        lst = press(lst, KeyType.ESC)
        assert not lst.filtering
        assert lst.filter_text == ""

    def test_filter_backspace(self):
        lst = make()
        lst = press(lst, KeyType.RUNES, "/")
        lst = press(lst, KeyType.RUNES, "x")
        lst = press(lst, KeyType.BACKSPACE)
        assert lst.filter_text == ""


class TestData:
    def test_set_items_resets_cursor(self):
        lst = make()
        lst = press(lst, KeyType.DOWN)
        lst.set_items([Item("New")])
        assert lst.cursor == 0
        assert len(lst.items) == 1


class TestView:
    def test_shows_title(self):
        assert "Snacks" in strip_ansi(make().view())

    def test_shows_items(self):
        view = strip_ansi(make().view())
        assert "Pocky" in view
        assert "Ramen" in view

    def test_status_bar(self):
        view = strip_ansi(make().view())
        assert "3 items" in view

    def test_empty_message(self):
        lst = List([], width=20, height=8)
        assert "no items" in strip_ansi(lst.view())

    def test_no_description(self):
        lst = make()
        lst.show_description = False
        view = strip_ansi(lst.view())
        assert "snack" not in view
