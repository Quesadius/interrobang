"""Tests for the testing helpers (feed / run_command / drive)."""

from interrobang import KeyMsg, KeyType, quit
from interrobang.testing import StepResult, drive, feed, run_command, strip_ansi


class Counter:
    def __init__(self):
        self.n = 0

    def init(self):
        return None

    def update(self, msg):
        if isinstance(msg, KeyMsg):
            if msg.key == "+":
                self.n += 1
            elif msg.key == "q":
                return self, quit
        return self, None

    def view(self):
        return f"n={self.n}"


class TestFeed:
    def test_returns_one_result_per_message(self):
        results = feed(Counter(), [KeyMsg(KeyType.RUNES, "+"), KeyMsg(KeyType.RUNES, "+")])
        assert len(results) == 2
        assert all(isinstance(r, StepResult) for r in results)

    def test_final_state(self):
        results = feed(Counter(), [KeyMsg(KeyType.RUNES, "+")] * 3)
        assert results[-1].model.n == 3
        assert results[-1].view == "n=3"

    def test_captures_command(self):
        results = feed(Counter(), [KeyMsg(KeyType.RUNES, "q")])
        assert results[-1].command is quit

    def test_empty_messages(self):
        assert feed(Counter(), []) == []

    def test_lenient_non_tuple_update(self):
        class Lenient:
            def update(self, msg):
                return self

            def view(self):
                return "ok"

        results = feed(Lenient(), [KeyMsg(KeyType.RUNES, "a")])
        assert results[-1].command is None
        assert results[-1].view == "ok"


class TestRunCommand:
    def test_executes_and_collects(self):
        assert run_command(lambda: "msg") == ["msg"]


class TestDrive:
    def test_returns_output_and_model(self):
        output, final = drive(Counter(), [KeyMsg(KeyType.RUNES, "+")])
        assert isinstance(output, str)
        assert final.n == 1


def test_strip_ansi_reexported():
    assert strip_ansi("\x1b[1mhi\x1b[0m") == "hi"
