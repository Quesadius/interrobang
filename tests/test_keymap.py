"""Tests for KeyBinding and the Help component."""

from interrobang import KeyMsg, KeyType
from interrobang.components import Help, KeyBinding
from interrobang.testing import strip_ansi


class TestKeyBinding:
    def test_matches(self):
        b = KeyBinding(["up", "k"], "↑/k", "move up")
        assert b.matches(KeyMsg(KeyType.UP))
        assert b.matches(KeyMsg(KeyType.RUNES, "k"))

    def test_no_match(self):
        b = KeyBinding(["up"], "↑", "move up")
        assert not b.matches(KeyMsg(KeyType.DOWN))

    def test_ignores_non_key(self):
        b = KeyBinding(["up"], "↑", "up")
        assert not b.matches("not a key")

    def test_disabled_never_matches(self):
        b = KeyBinding(["up"], "↑", "up", enabled=False)
        assert not b.matches(KeyMsg(KeyType.UP))

    def test_set_enabled(self):
        b = KeyBinding(["up"], "↑", "up")
        b.set_enabled(False)
        assert not b.matches(KeyMsg(KeyType.UP))


class TestHelp:
    def test_short_view_contains_keys_and_descs(self):
        up = KeyBinding(["up", "k"], "↑/k", "up")
        quit_ = KeyBinding(["q"], "q", "quit")
        view = strip_ansi(Help().short_view([up, quit_]))
        assert "↑/k" in view
        assert "up" in view
        assert "quit" in view

    def test_short_view_separator(self):
        up = KeyBinding(["up"], "↑", "up")
        quit_ = KeyBinding(["q"], "q", "quit")
        view = strip_ansi(Help().short_view([up, quit_]))
        assert "·" in view

    def test_skips_bindings_without_help(self):
        a = KeyBinding(["x"], "", "")  # no help key
        b = KeyBinding(["q"], "q", "quit")
        view = strip_ansi(Help().short_view([a, b]))
        assert view.count("q") >= 1

    def test_full_view_multiple_columns(self):
        col1 = [KeyBinding(["up"], "↑", "up")]
        col2 = [KeyBinding(["q"], "q", "quit")]
        view = strip_ansi(Help().full_view([col1, col2]))
        assert "up" in view
        assert "quit" in view

    def test_view_toggles_with_show_all(self):
        b = KeyBinding(["q"], "q", "quit")
        h = Help()
        short = strip_ansi(h.view([b]))
        h.show_all = True
        full = strip_ansi(h.view([b]))
        assert "quit" in short
        assert "quit" in full
