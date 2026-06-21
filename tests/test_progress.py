"""Tests for the Progress component."""

from interrobang._ansi import string_width
from interrobang.components import Progress
from interrobang.testing import strip_ansi


def test_empty_bar():
    v = strip_ansi(Progress(width=20).view_as(0.0))
    assert "█" not in v
    assert v.endswith("0%")


def test_full_bar():
    v = strip_ansi(Progress(width=20).view_as(1.0))
    assert "░" not in v
    assert v.endswith("100%")


def test_half_bar_has_both():
    v = strip_ansi(Progress(width=20).view_as(0.5))
    assert "█" in v
    assert "░" in v
    assert "50%" in v


def test_clamps_high():
    assert Progress(width=20).view_as(5.0) == Progress(width=20).view_as(1.0)


def test_clamps_low():
    assert Progress(width=20).view_as(-1.0) == Progress(width=20).view_as(0.0)


def test_set_percent():
    p = Progress(width=20)
    p.set_percent(0.3)
    assert p.percent == 0.3
    assert strip_ansi(p.view()) == strip_ansi(p.view_as(0.3))


def test_incr_percent_clamps():
    p = Progress(width=20)
    p.set_percent(0.9)
    p.incr_percent(0.5)
    assert p.percent == 1.0


def test_hide_percentage():
    p = Progress(width=20)
    p.show_percentage = False
    v = strip_ansi(p.view_as(0.5))
    assert "%" not in v
    assert string_width(v) == 20


def test_gradient_renders_colors():
    p = Progress(width=20).with_gradient("#FF7CCB", "#FDFF8C")
    out = p.view_as(0.5)
    assert "\x1b[" in out  # contains color escapes


def test_solid_color():
    p = Progress(width=20).with_solid("#7D56F4")
    out = p.view_as(0.5)
    assert "38;2;125;86;244" in out


def test_chainable():
    p = Progress(width=10)
    assert p.with_gradient("#000000", "#ffffff") is p
    assert p.with_solid("#ff0000") is p
