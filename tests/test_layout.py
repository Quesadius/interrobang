"""Tests for layout primitives: alignment, joining, placement."""

from interrobang._ansi import max_line_width, string_width
from interrobang.style import (
    BOTTOM,
    CENTER,
    LEFT,
    RIGHT,
    TOP,
    align_horizontal,
    align_vertical,
    join_horizontal,
    join_vertical,
    place,
    place_horizontal,
    place_vertical,
)
from interrobang.style.layout import pad_right


class TestPadRight:
    def test_pads(self):
        assert pad_right("ab", 5) == "ab   "

    def test_no_pad_when_wide_enough(self):
        assert pad_right("abcde", 3) == "abcde"

    def test_custom_fill(self):
        assert pad_right("ab", 5, ".") == "ab..."


class TestAlignHorizontal:
    def test_left(self):
        assert align_horizontal("ab", 5, LEFT) == "ab   "

    def test_right(self):
        assert align_horizontal("ab", 5, RIGHT) == "   ab"

    def test_center(self):
        assert align_horizontal("ab", 6, CENTER) == "  ab  "

    def test_multiline_becomes_rectangular(self):
        result = align_horizontal("a\nbbb", 3, LEFT)
        assert result == "a  \nbbb"

    def test_no_change_when_too_wide(self):
        assert align_horizontal("abcde", 3, LEFT) == "abcde"


class TestAlignVertical:
    def test_top(self):
        assert align_vertical("a", 3, TOP) == "a\n\n"

    def test_bottom(self):
        assert align_vertical("a", 3, BOTTOM) == "\n\na"

    def test_center(self):
        assert align_vertical("a", 3, CENTER) == "\na\n"

    def test_no_change_when_tall_enough(self):
        assert align_vertical("a\nb\nc", 2, TOP) == "a\nb\nc"


class TestJoinHorizontal:
    def test_side_by_side(self):
        result = join_horizontal(TOP, "a\nb", "1\n2")
        assert result == "a1\nb2"

    def test_uneven_heights_padded(self):
        result = join_horizontal(TOP, "a\nb\nc", "1")
        assert result.split("\n") == ["a1", "b ", "c "]

    def test_center_alignment(self):
        result = join_horizontal(CENTER, "a\nb\nc", "X")
        # X should sit on the middle row of the taller block.
        assert result.split("\n") == ["a ", "bX", "c "]

    def test_empty_blocks(self):
        assert join_horizontal(TOP) == ""

    def test_ignores_none(self):
        assert join_horizontal(TOP, "a", None) == "a"


class TestJoinVertical:
    def test_stacks(self):
        result = join_vertical(LEFT, "ab", "c")
        assert result == "ab\nc "

    def test_center(self):
        result = join_vertical(CENTER, "abc", "x")
        assert result == "abc\n x "

    def test_empty(self):
        assert join_vertical(LEFT) == ""


class TestPlace:
    def test_center_in_box(self):
        result = place(5, 3, CENTER, CENTER, "x")
        lines = result.split("\n")
        assert len(lines) == 3
        assert max_line_width(result) == 5
        assert "x" in lines[1]

    def test_place_horizontal(self):
        assert place_horizontal(5, RIGHT, "ab") == "   ab"

    def test_place_vertical_fills_width(self):
        result = place_vertical(3, TOP, "ab")
        lines = result.split("\n")
        assert all(string_width(line) == 2 for line in lines)

    def test_place_vertical_no_change(self):
        assert place_vertical(1, TOP, "a\nb") == "a\nb"
