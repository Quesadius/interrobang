"""Tests for the TextInput component."""

from interrobang import KeyMsg, KeyType
from interrobang.components import EchoMode, TextInput
from interrobang.testing import strip_ansi


def press(ti, key_type, runes="", **kw):
    return ti.update(KeyMsg(key_type, runes, **kw))[0]


def typestr(ti, text):
    for ch in text:
        ti = press(ti, KeyType.RUNES, ch)
    return ti


class TestTyping:
    def test_insert(self):
        ti = typestr(TextInput(), "hello")
        assert ti.value == "hello"
        assert ti.cursor == 5

    def test_insert_at_cursor(self):
        ti = typestr(TextInput(), "Joe")
        ti = press(ti, KeyType.LEFT)
        ti = press(ti, KeyType.RUNES, "X")
        assert ti.value == "JoXe"
        assert ti.cursor == 3

    def test_space(self):
        ti = typestr(TextInput(), "a")
        ti = press(ti, KeyType.SPACE, " ")
        ti = press(ti, KeyType.RUNES, "b")
        assert ti.value == "a b"


class TestCursorMovement:
    def test_left_right(self):
        ti = typestr(TextInput(), "abc")
        ti = press(ti, KeyType.LEFT)
        assert ti.cursor == 2
        ti = press(ti, KeyType.RIGHT)
        assert ti.cursor == 3

    def test_left_clamps(self):
        ti = TextInput()
        ti = press(ti, KeyType.LEFT)
        assert ti.cursor == 0

    def test_right_clamps(self):
        ti = typestr(TextInput(), "ab")
        ti = press(ti, KeyType.RIGHT)
        assert ti.cursor == 2

    def test_home_end(self):
        ti = typestr(TextInput(), "abc")
        ti = press(ti, KeyType.HOME)
        assert ti.cursor == 0
        ti = press(ti, KeyType.END)
        assert ti.cursor == 3

    def test_ctrl_a_e(self):
        ti = typestr(TextInput(), "abc")
        ti = press(ti, KeyType.RUNES, "a", ctrl=True)
        assert ti.cursor == 0
        ti = press(ti, KeyType.RUNES, "e", ctrl=True)
        assert ti.cursor == 3


class TestDeletion:
    def test_backspace(self):
        ti = typestr(TextInput(), "abc")
        ti = press(ti, KeyType.BACKSPACE)
        assert ti.value == "ab"
        assert ti.cursor == 2

    def test_backspace_at_start(self):
        ti = TextInput()
        ti = press(ti, KeyType.BACKSPACE)
        assert ti.value == ""

    def test_delete(self):
        ti = typestr(TextInput(), "abc")
        ti = press(ti, KeyType.HOME)
        ti = press(ti, KeyType.DELETE)
        assert ti.value == "bc"

    def test_ctrl_u(self):
        ti = typestr(TextInput(), "abc")
        ti = press(ti, KeyType.LEFT)
        ti = press(ti, KeyType.RUNES, "u", ctrl=True)
        assert ti.value == "c"
        assert ti.cursor == 0

    def test_ctrl_k(self):
        ti = typestr(TextInput(), "abc")
        ti = press(ti, KeyType.HOME)
        ti = press(ti, KeyType.RIGHT)
        ti = press(ti, KeyType.RUNES, "k", ctrl=True)
        assert ti.value == "a"

    def test_ctrl_w(self):
        ti = typestr(TextInput(), "foo bar")
        ti = press(ti, KeyType.RUNES, "w", ctrl=True)
        assert ti.value == "foo "


class TestLimits:
    def test_char_limit(self):
        ti = TextInput()
        ti.char_limit = 3
        ti = typestr(ti, "abcdef")
        assert ti.value == "abc"

    def test_set_value_respects_limit(self):
        ti = TextInput()
        ti.char_limit = 2
        ti.set_value("hello")
        assert ti.value == "he"


class TestState:
    def test_blur_ignores_input(self):
        ti = TextInput()
        ti.blur()
        ti = press(ti, KeyType.RUNES, "a")
        assert ti.value == ""

    def test_focus_reenables(self):
        ti = TextInput()
        ti.blur()
        ti.focus()
        ti = press(ti, KeyType.RUNES, "a")
        assert ti.value == "a"

    def test_reset(self):
        ti = typestr(TextInput(), "abc")
        ti.reset()
        assert ti.value == ""
        assert ti.cursor == 0


class TestView:
    def test_includes_prompt(self):
        ti = typestr(TextInput(), "hi")
        assert strip_ansi(ti.view()).startswith("> ")

    def test_placeholder_when_empty(self):
        ti = TextInput()
        ti.placeholder = "name"
        assert "name" in strip_ansi(ti.view())

    def test_password_mode(self):
        ti = typestr(TextInput(), "secret")
        ti.echo = EchoMode.PASSWORD
        visible = strip_ansi(ti.view())
        assert visible.startswith("> ••••••")  # trailing cell is the cursor
        assert visible.count("•") == 6

    def test_blurred_view_no_cursor(self):
        ti = typestr(TextInput(), "abc")
        ti.blur()
        assert strip_ansi(ti.view()) == "> abc"

    def test_blurred_placeholder(self):
        ti = TextInput()
        ti.placeholder = "name"
        ti.blur()
        assert strip_ansi(ti.view()) == "> name"

    def test_delete_at_end_noop(self):
        ti = typestr(TextInput(), "ab")  # cursor at end
        ti = press(ti, KeyType.DELETE)
        assert ti.value == "ab"

    def test_ctrl_w_at_start_noop(self):
        ti = TextInput()
        ti = press(ti, KeyType.RUNES, "w", ctrl=True)
        assert ti.value == ""

    def test_none_mode_hides(self):
        ti = typestr(TextInput(), "secret")
        ti.echo = EchoMode.NONE
        assert "secret" not in strip_ansi(ti.view())

    def test_horizontal_scroll(self):
        ti = TextInput()
        ti.width = 5
        ti = typestr(ti, "abcdefghij")
        visible = strip_ansi(ti.view())
        # Only the prompt plus a window of the text is shown.
        assert "j" in visible
        assert "a" not in visible.replace("> ", "", 1)
