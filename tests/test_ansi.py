"""Tests for the low-level ANSI/width engine."""

from interrobang._ansi import (
    char_width,
    max_line_width,
    string_width,
    strip_ansi,
    truncate,
    wrap,
)


class TestStripAnsi:
    def test_removes_sgr(self):
        assert strip_ansi("\x1b[1mbold\x1b[0m") == "bold"

    def test_removes_cursor_moves(self):
        assert strip_ansi("a\x1b[2Ab") == "ab"

    def test_removes_osc(self):
        assert strip_ansi("\x1b]0;title\x07x") == "x"

    def test_plain_text_unchanged(self):
        assert strip_ansi("hello") == "hello"


class TestCharWidth:
    def test_ascii_is_one(self):
        assert char_width("a") == 1

    def test_wide_is_two(self):
        assert char_width("世") == 2
        assert char_width("（") == 2  # fullwidth

    def test_combining_is_zero(self):
        assert char_width("́") == 0  # combining acute accent

    def test_control_is_zero(self):
        assert char_width("\x01") == 0
        assert char_width("\x7f") == 0

    def test_empty_is_zero(self):
        assert char_width("") == 0


class TestStringWidth:
    def test_plain(self):
        assert string_width("hello") == 5

    def test_ignores_ansi(self):
        assert string_width("\x1b[1mhi\x1b[0m") == 2

    def test_wide_chars(self):
        assert string_width("世界") == 4

    def test_max_line_width(self):
        assert max_line_width("a\nbbb\ncc") == 3

    def test_max_line_width_empty(self):
        assert max_line_width("") == 0


class TestTruncate:
    def test_no_truncation_needed(self):
        assert truncate("hello", 10) == "hello"

    def test_truncates(self):
        assert truncate("hello world", 5) == "hello"

    def test_truncates_with_tail(self):
        assert truncate("hello world", 5, "…") == "hell…"

    def test_zero_width(self):
        assert truncate("hello", 0) == ""

    def test_preserves_ansi_and_resets(self):
        result = truncate("\x1b[1mhello world\x1b[0m", 5)
        assert "\x1b[1m" in result
        assert result.endswith("\x1b[0m")
        assert string_width(result) == 5

    def test_respects_wide_chars(self):
        # 世 is width 2, so only one fits in width 3 (plus nothing else).
        assert truncate("世界", 3) == "世"


class TestWrap:
    def test_simple(self):
        assert wrap("the quick brown fox", 9) == "the quick\nbrown fox"

    def test_preserves_existing_newlines(self):
        assert wrap("a\nb", 10) == "a\nb"

    def test_hard_break_long_word(self):
        assert wrap("abcdefgh", 3) == "abc\ndef\ngh"

    def test_zero_width_returns_input(self):
        assert wrap("abc", 0) == "abc"

    def test_blank_lines_kept(self):
        assert wrap("a\n\nb", 5) == "a\n\nb"
