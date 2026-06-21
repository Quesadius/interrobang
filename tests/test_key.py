"""Tests for KeyMsg and its canonical naming."""

from interrobang.key import KeyMsg, KeyType


def test_rune():
    assert str(KeyMsg(KeyType.RUNES, "a")) == "a"


def test_uppercase_rune():
    assert str(KeyMsg(KeyType.RUNES, "A")) == "A"


def test_ctrl_rune():
    assert str(KeyMsg(KeyType.RUNES, "c", ctrl=True)) == "ctrl+c"


def test_alt_rune():
    assert str(KeyMsg(KeyType.RUNES, "a", alt=True)) == "alt+a"


def test_named_key():
    assert str(KeyMsg(KeyType.ENTER)) == "enter"
    assert str(KeyMsg(KeyType.ESC)) == "esc"
    assert str(KeyMsg(KeyType.BACKSPACE)) == "backspace"


def test_function_key():
    assert str(KeyMsg(KeyType.F1)) == "f1"
    assert str(KeyMsg(KeyType.F12)) == "f12"


def test_modified_named_key():
    assert str(KeyMsg(KeyType.UP, ctrl=True)) == "ctrl+up"
    assert str(KeyMsg(KeyType.TAB, shift=True)) == "shift+tab"


def test_modifier_order():
    msg = KeyMsg(KeyType.UP, alt=True, ctrl=True, shift=True)
    assert str(msg) == "ctrl+alt+shift+up"


def test_key_property():
    assert KeyMsg(KeyType.RUNES, "x").key == "x"
    assert KeyMsg(KeyType.RUNES, "c", ctrl=True).key == "ctrl+c"


def test_space():
    assert str(KeyMsg(KeyType.SPACE, " ")) == "space"


def test_equality_and_hash():
    assert KeyMsg(KeyType.RUNES, "a") == KeyMsg(KeyType.RUNES, "a")
    assert KeyMsg(KeyType.UP) != KeyMsg(KeyType.DOWN)
    # frozen dataclasses are hashable
    assert len({KeyMsg(KeyType.UP), KeyMsg(KeyType.UP)}) == 1
