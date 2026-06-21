"""Tests for the Style rendering engine."""

from interrobang.style import (
    CENTER,
    NORMAL,
    ROUNDED,
    Color,
    Profile,
    Style,
    get_color_profile,
    get_has_dark_background,
    set_color_profile,
    set_has_dark_background,
)
from interrobang._ansi import max_line_width, string_width, strip_ansi

RESET = "\x1b[0m"


class TestTextAttributes:
    def test_plain_has_no_escapes(self):
        assert Style().render("hi") == "hi"

    def test_bold(self):
        assert Style().bold().render("hi") == "\x1b[1mhi\x1b[0m"

    def test_italic(self):
        assert Style().italic().render("hi") == "\x1b[3mhi\x1b[0m"

    def test_underline(self):
        assert Style().underline().render("hi") == "\x1b[4mhi\x1b[0m"

    def test_combined_order(self):
        assert Style().bold().italic().underline().render("x") == "\x1b[1;3;4mx\x1b[0m"

    def test_all_attributes(self):
        s = Style().bold().faint().italic().underline().blink().reverse().strikethrough()
        assert s.render("x") == "\x1b[1;2;3;4;5;7;9mx\x1b[0m"

    def test_toggle_off(self):
        assert Style().bold().bold(False).render("x") == "x"


class TestColors:
    def test_foreground(self):
        assert Style().foreground(Color("#ff0066")).render("x") == "\x1b[38;2;255;0;102mx\x1b[0m"

    def test_background(self):
        assert Style().background(Color("#ff0066")).render("x") == "\x1b[48;2;255;0;102mx\x1b[0m"

    def test_foreground_and_background(self):
        s = Style().foreground(Color("#ffffff")).background(Color("#000000"))
        assert s.render("x") == "\x1b[38;2;255;255;255;48;2;0;0;0mx\x1b[0m"

    def test_unset_color(self):
        assert Style().foreground(Color("#fff")).foreground(None).render("x") == "x"

    def test_color_profile_override(self):
        s = Style().foreground(Color("#ff0000")).color_profile(Profile.ANSI)
        assert s.render("x") == "\x1b[91mx\x1b[0m"

    def test_string_and_int_color_args(self):
        assert Style().foreground("#ff0066").render("x") == Style().foreground(Color("#ff0066")).render("x")


class TestPadding:
    def test_horizontal_padding(self):
        assert Style().padding(0, 1).render("x") == " x "

    def test_all_around(self):
        result = Style().padding(1).render("x")
        assert result == "   \n x \n   "

    def test_background_fills_padding(self):
        result = Style().background(Color("#000000")).padding(0, 1).render("x")
        # The padding spaces carry the background color too.
        assert strip_ansi(result) == " x "
        assert result.count("48;2;0;0;0") >= 1


class TestSizing:
    def test_width_wraps(self):
        assert Style().width(5).render("hello world") == "hello\nworld"

    def test_width_pads_short_text(self):
        assert Style().width(5).render("ab") == "ab   "

    def test_height_pads(self):
        assert Style().height(3).render("a") == "a\n \n "

    def test_height_crops(self):
        assert Style().height(1).render("a\nb\nc") == "a"

    def test_max_width_truncates(self):
        assert Style().max_width(3).render("hello") == "hel"

    def test_max_height_limits_lines(self):
        assert Style().max_height(2).render("a\nb\nc") == "a\nb"


class TestAlignment:
    def test_center(self):
        assert Style().width(5).align(CENTER).render("ab") == "  ab "

    def test_vertical_center(self):
        result = Style().height(3).align_vertical(0.5).render("x")
        assert result == " \nx\n "


class TestBorder:
    def test_full_border(self):
        assert Style().border(NORMAL).render("ab") == "┌──┐\n│ab│\n└──┘"

    def test_default_border_is_normal(self):
        assert Style().border().render("ab") == "┌──┐\n│ab│\n└──┘"

    def test_partial_border_no_top(self):
        assert Style().border(NORMAL, top=False).render("ab") == "│ab│\n└──┘"

    def test_rounded(self):
        result = Style().border(ROUNDED).render("ab")
        assert result.startswith("╭")

    def test_border_color(self):
        result = Style().border(NORMAL).border_foreground(Color("#ff0000")).render("a")
        assert "38;2;255;0;0" in result


class TestMargin:
    def test_horizontal_margin(self):
        assert Style().margin(0, 1).render("a") == " a "

    def test_vertical_margin(self):
        assert Style().margin(1, 0).render("a") == " \na\n "

    def test_margin_background(self):
        result = Style().margin(0, 1).margin_background(Color("#ff0000")).render("a")
        assert "48;2;255;0;0" in result


class TestInline:
    def test_strips_newlines(self):
        assert Style().inline().render("a\nb") == "ab"

    def test_ignores_block_layout(self):
        assert Style().inline().padding(2).border(NORMAL).bold().render("x") == "\x1b[1mx\x1b[0m"


class TestTransform:
    def test_uppercase(self):
        assert Style().transform(str.upper).render("ab") == "AB"


class TestGetters:
    def test_get_width_height(self):
        s = Style().width(10).height(5)
        assert s.get_width() == 10
        assert s.get_height() == 5

    def test_padding_getters(self):
        s = Style().padding(1, 2, 3, 4)
        assert s.get_padding() == (1, 2, 3, 4)
        assert s.horizontal_padding() == 6
        assert s.vertical_padding() == 4

    def test_frame_sizes(self):
        s = Style().padding(1, 2).margin(1, 2).border(NORMAL)
        # horizontal: padding 4 + margin 4 + 2 border = 10
        assert s.horizontal_frame_size() == 10
        # vertical: padding 2 + margin 2 + 2 border = 6
        assert s.vertical_frame_size() == 6

    def test_individual_edge_setters(self):
        s = Style().padding_top(1).padding_right(2).padding_bottom(3).padding_left(4)
        assert s.get_padding() == (1, 2, 3, 4)

    def test_individual_margin_setters(self):
        s = Style().margin_top(1).margin_right(2).margin_bottom(3).margin_left(4)
        assert s.get_margin() == (1, 2, 3, 4)


class TestInherit:
    def test_inherits_unset_attributes(self):
        parent = Style().bold().foreground(Color("#ff0000"))
        child = Style().italic().inherit(parent)
        out = child.render("x")
        assert "1" in out.split("m")[0]  # bold inherited
        assert "3" in out.split("m")[0]  # italic kept
        assert "38;2;255;0;0" in out  # color inherited

    def test_own_value_wins(self):
        parent = Style().bold(True)
        child = Style().foreground(Color("#00ff00")).inherit(parent)
        assert "38;2;0;255;0" in child.render("x")


class TestImmutability:
    def test_setters_return_new_instances(self):
        base = Style()
        bold = base.bold()
        assert base is not bold
        assert base.render("x") == "x"
        assert bold.render("x") == "\x1b[1mx\x1b[0m"

    def test_copy(self):
        base = Style().bold()
        assert base.copy().render("x") == base.render("x")

    def test_callable_alias(self):
        s = Style().bold()
        assert s("x") == s.render("x")


class TestProfileGlobals:
    def test_set_and_get_profile(self):
        set_color_profile(Profile.ANSI)
        assert get_color_profile() == Profile.ANSI
        set_color_profile(Profile.TRUECOLOR)

    def test_set_and_get_dark(self):
        set_has_dark_background(False)
        assert get_has_dark_background() is False
        set_has_dark_background(True)


def test_render_joins_multiple_parts():
    assert Style().render("a", "b", "c") == "a b c"


def test_render_coerces_non_strings():
    assert Style().render(42) == "42"
