"""Integration tests for the Program event loop (run headlessly)."""

import io
import threading

from interrobang import KeyMsg, KeyType, WindowSizeMsg, quit, run
from interrobang.command import (
    clear_screen,
    disable_mouse,
    enable_mouse,
    enter_alt_screen,
    exit_alt_screen,
    hide_cursor,
    set_window_title,
    show_cursor,
)
from interrobang.program import Program, detect_dark_background, detect_profile
from interrobang.style import Profile
from interrobang.testing import drive, strip_ansi


class App:
    def __init__(self):
        self.keys: list[str] = []
        self.size = None
        self.count = 0

    def init(self):
        return None

    def update(self, msg):
        if isinstance(msg, WindowSizeMsg):
            self.size = (msg.width, msg.height)
        elif isinstance(msg, KeyMsg):
            self.keys.append(msg.key)
            if msg.key == "+":
                self.count += 1
        return self, None

    def view(self):
        return f"count={self.count}"


def _run_in_thread(program: Program):
    errors: list[BaseException] = []

    def target():
        try:
            program.run()
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    thread = threading.Thread(target=target)
    thread.start()
    return thread, errors


class TestDrive:
    def test_applies_messages(self):
        _, final = drive(App(), [KeyMsg(KeyType.RUNES, "+"), KeyMsg(KeyType.RUNES, "+")])
        assert final.count == 2
        assert final.keys == ["+", "+"]

    def test_initial_window_size(self):
        _, final = drive(App(), [])
        assert final.size == (80, 24)  # headless default size

    def test_output_contains_view(self):
        out, _ = drive(App(), [KeyMsg(KeyType.RUNES, "+")])
        assert "count=1" in strip_ansi(out)


class TestControlMessages:
    def test_control_messages_do_not_crash(self):
        messages = [
            enter_alt_screen(),
            exit_alt_screen(),
            hide_cursor(),
            show_cursor(),
            enable_mouse(),
            disable_mouse(),
            clear_screen(),
            set_window_title("hi")(),
        ]
        out, final = drive(App(), messages)
        # Control messages are intercepted, never reaching update.
        assert final.keys == []


class TestInterrupt:
    def test_ctrl_c_quits_by_default(self):
        program = Program(App(), output=io.StringIO(), headless=True)
        thread, errors = _run_in_thread(program)
        program.send(KeyMsg(KeyType.RUNES, "c", ctrl=True))
        thread.join(timeout=3.0)
        assert not thread.is_alive()
        assert errors == []

    def test_ctrl_c_delivered_when_not_caught(self):
        _, final = drive(App(), [KeyMsg(KeyType.RUNES, "c", ctrl=True)])
        assert "ctrl+c" in final.keys


class TestCommandErrors:
    def test_command_error_surfaces(self):
        def boom():
            raise RuntimeError("boom")

        class Boom:
            def init(self):
                return None

            def update(self, msg):
                if isinstance(msg, KeyMsg):
                    return self, boom
                return self, None

            def view(self):
                return "x"

        program = Program(Boom(), output=io.StringIO(), headless=True, catch_interrupt=False)
        thread, errors = _run_in_thread(program)
        program.send(KeyMsg(KeyType.RUNES, "a"))
        thread.join(timeout=3.0)
        assert len(errors) == 1
        assert isinstance(errors[0], RuntimeError)


class TestLenientUpdate:
    def test_model_only_return(self):
        class Lenient:
            def init(self):
                return None

            def update(self, msg):
                return self  # no command tuple

            def view(self):
                return "ok"

        out, final = drive(Lenient(), [KeyMsg(KeyType.RUNES, "a")])
        assert "ok" in strip_ansi(out)


class TestRunConvenience:
    def test_run_quits_from_init(self):
        class QuitNow:
            def init(self):
                return quit

            def update(self, msg):
                return self, None

            def view(self):
                return "bye"

        final = run(QuitNow(), output=io.StringIO(), headless=True)
        assert final.view() == "bye"


class QuitOnQ:
    def __init__(self):
        self.count = 0

    def init(self):
        return None

    def update(self, msg):
        if isinstance(msg, KeyMsg):
            if msg.key == "q":
                return self, quit
            if msg.key == "+":
                self.count += 1
        return self, None

    def view(self):
        return f"count={self.count}"


class TestRealInputStream:
    def test_reads_and_parses_input_bytes(self):
        # A binary input stream exercises the real input-reader thread, byte
        # parsing, and EOF handling -- without needing a TTY.
        program = Program(
            QuitOnQ(),
            input=io.BytesIO(b"++q"),
            output=io.StringIO(),
            headless=True,
        )
        final = program.run()
        assert final.count == 2

    def test_arrow_keys_through_stream(self):
        class Tracker:
            def __init__(self):
                self.keys = []

            def init(self):
                return None

            def update(self, msg):
                if isinstance(msg, KeyMsg):
                    self.keys.append(msg.key)
                    if msg.key == "q":
                        return self, quit
                return self, None

            def view(self):
                return ""

        program = Program(
            Tracker(), input=io.BytesIO(b"\x1b[A\x1b[Bq"), output=io.StringIO(), headless=True
        )
        final = program.run()
        assert final.keys[:2] == ["up", "down"]


class Trigger:
    """A plain custom message used to kick off a command in tests."""


class TestSequenceAndBatchCommands:
    def _run(self, command_factory):
        from interrobang.command import batch, sequence  # noqa: F401

        class SeqModel:
            def __init__(self):
                self.got = []

            def init(self):
                return None

            def update(self, msg):
                if isinstance(msg, Trigger):
                    return self, command_factory()
                if isinstance(msg, tuple) and msg and msg[0] == "m":
                    self.got.append(msg[1])
                    if len(self.got) >= 2:
                        return self, quit
                return self, None

            def view(self):
                return ""

        program = Program(SeqModel(), output=io.StringIO(), headless=True, catch_interrupt=False)
        thread, errors = _run_in_thread(program)
        program.send(Trigger())
        thread.join(timeout=3.0)
        assert errors == []
        return program.final_model

    def test_sequence_runs_in_order(self):
        from interrobang.command import sequence

        final = self._run(lambda: sequence(lambda: ("m", "a"), lambda: ("m", "b")))
        assert final.got == ["a", "b"]

    def test_batch_runs_all(self):
        from interrobang.command import batch

        final = self._run(lambda: batch(lambda: ("m", "a"), lambda: ("m", "b")))
        assert sorted(final.got) == ["a", "b"]

    def test_nested_sequence_and_batch(self):
        from interrobang.command import batch, sequence

        final = self._run(
            lambda: sequence(sequence(lambda: ("m", "a")), batch(lambda: ("m", "b")))
        )
        assert final.got == ["a", "b"]

    def test_error_inside_sequence_surfaces(self):
        from interrobang.command import sequence

        def boom():
            raise RuntimeError("seq boom")

        class M:
            def init(self):
                return None

            def update(self, msg):
                if isinstance(msg, Trigger):
                    return self, sequence(boom, lambda: None)
                return self, None

            def view(self):
                return ""

        program = Program(M(), output=io.StringIO(), headless=True, catch_interrupt=False)
        thread, errors = _run_in_thread(program)
        program.send(Trigger())
        thread.join(timeout=3.0)
        assert len(errors) == 1
        assert isinstance(errors[0], RuntimeError)


class TestInputEofFlush:
    def test_eof_flushes_pending_escape(self):
        class QuitOnEsc:
            def init(self):
                return None

            def update(self, msg):
                if isinstance(msg, KeyMsg) and msg.key == "esc":
                    return self, quit
                return self, None

            def view(self):
                return ""

        # A lone ESC is incomplete until EOF; the reader must flush it as Escape.
        program = Program(
            QuitOnEsc(), input=io.BytesIO(b"\x1b"), output=io.StringIO(), headless=True
        )
        program.run()  # returns only if ESC was delivered and triggered quit


class TestAltScreenDrive:
    def test_alt_screen_output(self):
        out, _ = drive(App(), [KeyMsg(KeyType.RUNES, "+")], alt_screen=True)
        assert "\x1b[H" in out  # alt-screen renderer homes the cursor


class _Hi:
    def init(self):
        return None

    def update(self, msg):
        return self, None

    def view(self):
        return "hi"


class TestFillBackground:
    def test_paints_theme_background(self, monkeypatch):
        monkeypatch.setenv("COLORTERM", "truecolor")
        buf = io.StringIO()
        program = Program(
            _Hi(), output=buf, headless=True, alt_screen=True,
            fill_background=True, catch_interrupt=False,
        )
        thread, errors = _run_in_thread(program)
        program.quit()
        thread.join(timeout=3.0)
        assert "48;2;0;43;54" in buf.getvalue()  # Solarized Dark background

    def test_no_fill_without_alt_screen(self, monkeypatch):
        monkeypatch.setenv("COLORTERM", "truecolor")
        buf = io.StringIO()
        program = Program(
            _Hi(), output=buf, headless=True, alt_screen=False,
            fill_background=True, catch_interrupt=False,
        )
        thread, errors = _run_in_thread(program)
        program.quit()
        thread.join(timeout=3.0)
        assert "48;2;0;43;54" not in buf.getvalue()

    def test_fill_follows_active_theme(self, monkeypatch):
        from interrobang import SOLARIZED_LIGHT, set_theme

        monkeypatch.setenv("COLORTERM", "truecolor")
        set_theme(SOLARIZED_LIGHT)
        buf = io.StringIO()
        program = Program(
            _Hi(), output=buf, headless=True, alt_screen=True,
            fill_background=True, catch_interrupt=False,
        )
        thread, errors = _run_in_thread(program)
        program.quit()
        thread.join(timeout=3.0)
        assert "48;2;253;246;227" in buf.getvalue()  # Solarized Light background


class TestDetectProfile:
    def test_no_color(self):
        assert detect_profile({"NO_COLOR": "1"}) == Profile.ASCII

    def test_truecolor(self):
        assert detect_profile({"COLORTERM": "truecolor"}) == Profile.TRUECOLOR

    def test_256(self):
        assert detect_profile({"TERM": "xterm-256color"}) == Profile.ANSI256

    def test_basic_color(self):
        assert detect_profile({"TERM": "xterm-color"}) == Profile.ANSI

    def test_not_tty_disables_color(self):
        assert detect_profile({"TERM": "xterm-256color"}, is_tty=False) == Profile.ASCII

    def test_force_color_when_not_tty(self):
        assert detect_profile({"COLORTERM": "truecolor"}, is_tty=False) == Profile.TRUECOLOR

    def test_dumb_terminal(self):
        assert detect_profile({"TERM": "dumb"}) == Profile.ASCII


class TestDetectDarkBackground:
    def test_dark(self):
        assert detect_dark_background({"COLORFGBG": "15;0"}) is True

    def test_light(self):
        assert detect_dark_background({"COLORFGBG": "0;15"}) is False

    def test_default_dark(self):
        assert detect_dark_background({}) is True
