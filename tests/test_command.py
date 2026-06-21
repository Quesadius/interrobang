"""Tests for commands and command combinators."""

from interrobang.command import (
    BatchCmd,
    SequenceCmd,
    _ClearScreen,
    _DisableMouse,
    _EnableMouse,
    _EnterAltScreen,
    _ExitAltScreen,
    _HideCursor,
    _SetWindowTitle,
    _ShowCursor,
    batch,
    clear_screen,
    disable_mouse,
    enable_mouse,
    enter_alt_screen,
    every,
    exit_alt_screen,
    hide_cursor,
    quit,
    sequence,
    set_window_title,
    show_cursor,
    tick,
)
from interrobang.message import QuitMsg
from interrobang.testing import run_command


def test_quit_returns_quit_msg():
    assert isinstance(quit(), QuitMsg)


class TestBatch:
    def test_none_when_empty(self):
        assert batch() is None
        assert batch(None, None) is None

    def test_single_passes_through(self):
        cmd = lambda: None
        assert batch(cmd) is cmd

    def test_multiple_makes_batchcmd(self):
        a, b = (lambda: 1), (lambda: 2)
        result = batch(a, b)
        assert isinstance(result, BatchCmd)
        assert result.cmds == (a, b)

    def test_filters_none(self):
        a = lambda: 1
        result = batch(a, None, a)
        assert isinstance(result, BatchCmd)
        assert len(result.cmds) == 2


class TestSequence:
    def test_none_when_empty(self):
        assert sequence() is None

    def test_makes_sequencecmd(self):
        a, b = (lambda: 1), (lambda: 2)
        result = sequence(a, b)
        assert isinstance(result, SequenceCmd)


class TestTick:
    def test_fires_message(self):
        msgs = run_command(tick(0, lambda t: ("tick", t)))
        assert len(msgs) == 1
        assert msgs[0][0] == "tick"
        assert isinstance(msgs[0][1], float)

    def test_every_fires_message(self):
        msgs = run_command(every(0.01, lambda t: "every"))
        assert msgs == ["every"]


class TestRunCommand:
    def test_none(self):
        assert run_command(None) == []

    def test_flattens_batch(self):
        msgs = run_command(batch(lambda: "a", lambda: "b"))
        assert msgs == ["a", "b"]

    def test_flattens_sequence(self):
        msgs = run_command(sequence(lambda: "a", lambda: "b"))
        assert msgs == ["a", "b"]

    def test_drops_none_results(self):
        assert run_command(lambda: None) == []


class TestControlCommands:
    def test_enter_alt_screen(self):
        assert isinstance(enter_alt_screen(), _EnterAltScreen)

    def test_exit_alt_screen(self):
        assert isinstance(exit_alt_screen(), _ExitAltScreen)

    def test_hide_cursor(self):
        assert isinstance(hide_cursor(), _HideCursor)

    def test_show_cursor(self):
        assert isinstance(show_cursor(), _ShowCursor)

    def test_enable_mouse(self):
        assert isinstance(enable_mouse(), _EnableMouse)

    def test_disable_mouse(self):
        assert isinstance(disable_mouse(), _DisableMouse)

    def test_clear_screen(self):
        assert isinstance(clear_screen(), _ClearScreen)

    def test_set_window_title(self):
        cmd = set_window_title("hi")
        msg = cmd()
        assert isinstance(msg, _SetWindowTitle)
        assert msg.title == "hi"
