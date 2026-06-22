"""Shared test fixtures and deterministic defaults.

The styling engine reads a module-wide color profile and background mode. We pin
both here so style output is identical regardless of the environment the tests
run in (CI, a piped shell, a fancy terminal, ...).
"""

import pytest

from interrobang.style import (
    Profile,
    get_color_profile,
    get_has_dark_background,
    set_color_profile,
    set_has_dark_background,
)
from interrobang.theme import SOLARIZED_DARK, get_theme, set_theme


@pytest.fixture(autouse=True)
def deterministic_color(request):
    """Force truecolor + dark background + the default theme for every test."""
    prev_profile = get_color_profile()
    prev_dark = get_has_dark_background()
    prev_theme = get_theme()
    set_color_profile(Profile.TRUECOLOR)
    set_has_dark_background(True)
    set_theme(SOLARIZED_DARK)
    yield
    set_color_profile(prev_profile)
    set_has_dark_background(prev_dark)
    set_theme(prev_theme)
