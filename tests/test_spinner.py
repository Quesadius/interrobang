"""Tests for the Spinner component."""

from interrobang.components import DOTS, LINE, Spinner, SpinnerTickMsg
from interrobang.style import Style
from interrobang.testing import strip_ansi


def test_initial_frame():
    s = Spinner(DOTS)
    assert strip_ansi(s.view()) == DOTS.frames[0]


def test_default_style_uses_theme_color():
    # With no explicit style, the spinner picks up the theme's selection color.
    assert "\x1b[" in Spinner(DOTS).view()


def test_tick_advances_frame():
    s = Spinner(DOTS)
    s, cmd = s.update(SpinnerTickMsg(s.id))
    assert s.frame == 1
    assert callable(cmd)


def test_frame_wraps_around():
    s = Spinner(LINE)
    for _ in range(len(LINE.frames)):
        s, _ = s.update(SpinnerTickMsg(s.id))
    assert s.frame == 0


def test_ignores_other_spinner_id():
    s = Spinner(DOTS)
    s, cmd = s.update(SpinnerTickMsg(s.id + 999))
    assert s.frame == 0
    assert cmd is None


def test_ignores_unrelated_message():
    s = Spinner(DOTS)
    s, cmd = s.update("not a tick")
    assert s.frame == 0
    assert cmd is None


def test_unique_ids():
    assert Spinner().id != Spinner().id


def test_tick_command_produces_message():
    s = Spinner(LINE)
    msg = s.tick()
    assert isinstance(msg, SpinnerTickMsg)
    assert msg.id == s.id


def test_style_applied():
    s = Spinner(LINE, Style().bold())
    assert s.view() == "\x1b[1m|\x1b[0m"
    assert strip_ansi(s.view()) == "|"
