"""Tests for the theme system."""

import dataclasses

import pytest

from interrobang import (
    NEON,
    SOLARIZED_DARK,
    SOLARIZED_LIGHT,
    Color,
    Style,
    Theme,
    get_theme,
    set_theme,
)
from interrobang.components import DOTS, Item, List, Progress, Spinner


def test_default_theme_is_solarized():
    # conftest pins the default theme for every test.
    assert get_theme() is SOLARIZED_DARK


def test_set_and_get_theme():
    set_theme(NEON)
    assert get_theme() is NEON
    set_theme(SOLARIZED_DARK)
    assert get_theme() is SOLARIZED_DARK


def test_theme_is_frozen():
    with pytest.raises(dataclasses.FrozenInstanceError):
        SOLARIZED_DARK.primary = "#000000"  # type: ignore[misc]


def test_progress_gradient_follows_solarized():
    out = Progress(width=20).view_as(1.0)
    assert "38;2;38;139;210" in out  # solarized blue (gradient start)


def test_progress_gradient_follows_neon():
    set_theme(NEON)
    out = Progress(width=20).view_as(1.0)
    assert "38;2;255;124;203" in out  # neon pink (gradient start)


def test_list_title_uses_theme_primary():
    lst = List([Item("a")], width=20, height=6)
    lst.title = "X"
    assert "48;2;38;139;210" in lst.view()  # solarized blue background


def test_list_title_recolors_with_neon():
    set_theme(NEON)
    lst = List([Item("a")], width=20, height=6)
    lst.title = "X"
    assert "48;2;125;86;244" in lst.view()  # neon purple background


def test_spinner_uses_theme_selection():
    out = Spinner(DOTS).view()
    assert "38;2;203;75;22" in out  # solarized orange


def test_custom_theme():
    custom = Theme(
        name="Test",
        background="#000000",
        surface="#111111",
        text="#ffffff",
        primary="#ff0000",
        secondary="#00ff00",
        selection="#0000ff",
        on_primary="#ffffff",
        on_selection="#000000",
        bright="#ffffff",
        muted="#888888",
        subtle="#999999",
        faint="#444444",
        gradient_start="#ff0000",
        gradient_end="#0000ff",
    )
    set_theme(custom)
    assert "38;2;0;0;255" in Spinner(DOTS).view()  # custom selection (blue)


def test_themes_have_distinct_names():
    assert SOLARIZED_DARK.name == "Solarized Dark"
    assert SOLARIZED_LIGHT.name == "Solarized Light"
    assert NEON.name == "Neon"


def test_solarized_light_uses_light_background():
    assert SOLARIZED_LIGHT.background == "#fdf6e3"
    set_theme(SOLARIZED_LIGHT)
    lst = List([Item("a")], width=20, height=6)
    lst.title = "X"
    assert "48;2;38;139;210" in lst.view()  # primary still blue


def test_set_theme_restyles_existing_component():
    lst = List([Item("a")], width=20, height=6)
    lst.title = "X"
    assert "48;2;38;139;210" in lst.view()  # solarized blue
    set_theme(NEON)
    assert "48;2;125;86;244" in lst.view()  # the SAME instance is now neon purple
    set_theme(SOLARIZED_DARK)
    assert "48;2;38;139;210" in lst.view()  # and back


def test_set_theme_preserves_explicit_spinner_style():
    sp = Spinner(DOTS, Style().foreground(Color("#ff00ff")))
    set_theme(NEON)
    assert "38;2;255;0;255" in sp.view()  # explicit style survives a theme switch


def test_set_theme_preserves_custom_progress_fill():
    bar = Progress(width=20).with_solid("#ff0000")
    set_theme(NEON)
    assert "38;2;255;0;0" in bar.view_as(1.0)  # custom fill survives a theme switch
