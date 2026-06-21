"""Tests for colors, profiles, and color degradation."""

import pytest

from interrobang.style import (
    ANSIColor,
    AdaptiveColor,
    Color,
    CompleteColor,
    NoColor,
    Profile,
    ansi256_to_rgb,
    parse_color,
    parse_hex,
    rgb_to_ansi16,
    rgb_to_ansi256,
)
from interrobang.style.color import TerminalColor


class TestParseHex:
    def test_full(self):
        assert parse_hex("#ff0066") == (255, 0, 102)

    def test_no_hash(self):
        assert parse_hex("ff0066") == (255, 0, 102)

    def test_shorthand(self):
        assert parse_hex("#f06") == (255, 0, 102)

    def test_invalid_length(self):
        with pytest.raises(ValueError):
            parse_hex("#ff00")

    def test_invalid_chars(self):
        with pytest.raises(ValueError):
            parse_hex("#gggggg")


class TestConversions:
    def test_rgb_to_ansi256_red(self):
        assert rgb_to_ansi256(255, 0, 0) == 196

    def test_rgb_to_ansi256_grayscale(self):
        # Mid gray should pick from the grayscale ramp (232-255).
        idx = rgb_to_ansi256(128, 128, 128)
        assert 232 <= idx <= 255

    def test_rgb_to_ansi256_pure_black(self):
        assert rgb_to_ansi256(0, 0, 0) == 16

    def test_rgb_to_ansi256_pure_white(self):
        assert rgb_to_ansi256(255, 255, 255) == 231

    def test_ansi256_to_rgb_roundtrip_base(self):
        assert ansi256_to_rgb(9) == (255, 0, 0)

    def test_ansi256_to_rgb_cube(self):
        assert ansi256_to_rgb(196) == (255, 0, 0)

    def test_ansi256_to_rgb_grayscale(self):
        r, g, b = ansi256_to_rgb(232)
        assert r == g == b == 8

    def test_rgb_to_ansi16_red(self):
        assert rgb_to_ansi16(255, 0, 0) == 9

    def test_rgb_to_ansi16_black(self):
        assert rgb_to_ansi16(0, 0, 0) == 0


class TestColor:
    def test_hex_truecolor(self):
        assert Color("#ff0066").sequence(Profile.TRUECOLOR, True, background=False) == "38;2;255;0;102"

    def test_hex_background(self):
        assert Color("#ff0066").sequence(Profile.TRUECOLOR, True, background=True) == "48;2;255;0;102"

    def test_hex_degrades_to_256(self):
        assert Color("#ff0000").sequence(Profile.ANSI256, True, background=False) == "38;5;196"

    def test_hex_degrades_to_ansi(self):
        assert Color("#ff0000").sequence(Profile.ANSI, True, background=False) == "91"

    def test_ascii_is_empty(self):
        assert Color("#ff0000").sequence(Profile.ASCII, True, background=False) == ""

    def test_base_index_ansi(self):
        assert Color(5).sequence(Profile.ANSI, True, background=False) == "35"

    def test_base_index_256(self):
        assert Color(5).sequence(Profile.ANSI256, True, background=False) == "38;5;5"

    def test_base_index_background_low(self):
        assert Color(3).sequence(Profile.ANSI, True, background=True) == "43"

    def test_bright_index_background(self):
        assert Color(12).sequence(Profile.ANSI256, True, background=True) == "48;5;12"

    def test_extended_index(self):
        assert Color(212).sequence(Profile.TRUECOLOR, True, background=False) == "38;5;212"

    def test_extended_index_degrades_to_ansi(self):
        seq = Color(212).sequence(Profile.ANSI, True, background=False)
        assert seq.isdigit() or ";" not in seq  # a single ansi code

    def test_string_index(self):
        assert Color("5").sequence(Profile.ANSI, True, background=False) == "35"

    def test_index_out_of_range(self):
        with pytest.raises(ValueError):
            Color(300).sequence(Profile.TRUECOLOR, True, background=False)

    def test_from_rgb(self):
        assert Color.from_rgb(255, 0, 102) == Color("#ff0066")


class TestANSIColor:
    def test_valid(self):
        assert ANSIColor(3).sequence(Profile.ANSI, True, background=False) == "33"

    def test_promotes_to_256(self):
        assert ANSIColor(3).sequence(Profile.ANSI256, True, background=False) == "38;5;3"

    def test_ascii(self):
        assert ANSIColor(3).sequence(Profile.ASCII, True, background=False) == ""

    def test_out_of_range(self):
        with pytest.raises(ValueError):
            ANSIColor(16)


class TestAdaptiveColor:
    def test_dark(self):
        c = AdaptiveColor(light="#000000", dark="#ffffff")
        assert c.sequence(Profile.TRUECOLOR, True, background=False) == "38;2;255;255;255"

    def test_light(self):
        c = AdaptiveColor(light="#000000", dark="#ffffff")
        assert c.sequence(Profile.TRUECOLOR, False, background=False) == "38;2;0;0;0"


class TestCompleteColor:
    def test_truecolor(self):
        c = CompleteColor(true_color="#ff0000", ansi256=196, ansi=9)
        assert c.sequence(Profile.TRUECOLOR, True, background=False) == "38;2;255;0;0"

    def test_ansi256(self):
        c = CompleteColor(true_color="#ff0000", ansi256=196, ansi=9)
        assert c.sequence(Profile.ANSI256, True, background=False) == "38;5;196"

    def test_ansi(self):
        c = CompleteColor(true_color="#ff0000", ansi256=196, ansi=9)
        assert c.sequence(Profile.ANSI, True, background=False) == "91"

    def test_fallback_when_field_missing(self):
        c = CompleteColor(true_color="#ff0000")
        assert c.sequence(Profile.ANSI256, True, background=False) == "38;5;196"

    def test_ascii(self):
        c = CompleteColor(true_color="#ff0000")
        assert c.sequence(Profile.ASCII, True, background=False) == ""

    def test_empty(self):
        assert CompleteColor().sequence(Profile.TRUECOLOR, True, background=False) == ""


class TestNoColor:
    def test_empty_sequence(self):
        assert NoColor().sequence(Profile.TRUECOLOR, True, background=False) == ""

    def test_equality(self):
        assert NoColor() == NoColor()
        assert NoColor() != Color("#fff")

    def test_repr(self):
        assert repr(NoColor()) == "NoColor()"

    def test_hashable(self):
        assert len({NoColor(), NoColor()}) == 1

    def test_resolve_is_none(self):
        assert NoColor().resolve(Profile.TRUECOLOR, True) is None


class TestParseColor:
    def test_passthrough(self):
        c = Color("#fff")
        assert parse_color(c) is c

    def test_string(self):
        assert parse_color("#ff0066") == Color("#ff0066")

    def test_int(self):
        assert parse_color(212) == Color(212)


def test_base_class_not_implemented():
    with pytest.raises(NotImplementedError):
        TerminalColor().resolve(Profile.TRUECOLOR, True)
