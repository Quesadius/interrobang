"""Tests for border presets and custom borders."""

from interrobang.style import (
    ASCII,
    BLOCK,
    DOUBLE,
    HIDDEN,
    MARKDOWN,
    NORMAL,
    ROUNDED,
    THICK,
    Border,
)


def test_normal_corners():
    assert NORMAL.top_left == "┌"
    assert NORMAL.bottom_right == "┘"


def test_rounded_corners():
    assert ROUNDED.top_left == "╭"
    assert ROUNDED.bottom_right == "╯"


def test_thick_edges():
    assert THICK.top == "━"
    assert THICK.left == "┃"


def test_double_edges():
    assert DOUBLE.top == "═"


def test_hidden_is_spaces():
    assert HIDDEN.top == " "
    assert HIDDEN.top_left == " "


def test_ascii_uses_plus():
    assert ASCII.top_left == "+"
    assert ASCII.top == "-"


def test_markdown_pipes():
    assert MARKDOWN.left == "|"


def test_block_filled():
    assert BLOCK.top == "█"


def test_custom_border_defaults_to_space():
    b = Border(top="*")
    assert b.top == "*"
    assert b.bottom == " "  # unspecified defaults to a space


def test_junctions_present_for_tables():
    assert NORMAL.middle == "┼"
    assert NORMAL.middle_top == "┬"
