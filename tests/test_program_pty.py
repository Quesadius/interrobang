"""Exercise the real terminal-management paths using a pseudo-terminal.

These tests run the Program against an actual PTY so the raw-mode, alt-screen,
cursor, and mouse setup/teardown code (which is skipped in headless mode) is
covered. They are POSIX-only and skipped where ``pty`` is unavailable.
"""

import os
import threading
import time

import pytest

pty = pytest.importorskip("pty")

from interrobang import KeyMsg, quit
from interrobang.program import Program


class QuitModel:
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
        return "press q"


def _run_against_pty(model, to_send: bytes, **program_kwargs):
    master, slave = pty.openpty()
    reader = os.fdopen(slave, "rb", buffering=0)
    writer = os.fdopen(os.dup(slave), "w")
    program = Program(model, input=reader, output=writer, **program_kwargs)

    errors = []

    def target():
        try:
            program.run()
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    # Continuously drain the master end. Without this, the program's output sits
    # in the PTY buffer and restore()'s TCSADRAIN (drain-on-restore) blocks. A
    # real terminal reads its output continuously, so this mirrors reality.
    def drain():
        try:
            while True:
                if not os.read(master, 4096):
                    break
        except OSError:
            pass

    drainer = threading.Thread(target=drain, daemon=True)
    drainer.start()

    thread = threading.Thread(target=target)
    thread.start()
    try:
        # Let the program enter raw mode before sending input; otherwise the tty
        # driver line-buffers our keystrokes in canonical mode (like a real user
        # who starts typing once the app is up).
        time.sleep(0.2)
        os.write(master, to_send)
        thread.join(timeout=5.0)
    finally:
        try:
            reader.close()
        except OSError:
            pass
        try:
            writer.close()
        except OSError:
            pass
        os.close(master)
        drainer.join(timeout=1.0)
    return program, thread, errors


def test_runs_against_real_tty():
    model = QuitModel()
    program, thread, errors = _run_against_pty(model, b"q")
    assert not thread.is_alive()
    assert errors == []
    assert "q" in program.final_model.keys


def test_alt_screen_and_mouse_setup_teardown():
    # Turning on the alt screen and mouse exercises the corresponding terminal
    # control on both setup and teardown.
    model = QuitModel()
    program, thread, errors = _run_against_pty(model, b"q", alt_screen=True, mouse=True)
    assert not thread.is_alive()
    assert errors == []


def test_input_arrives_in_pieces():
    model = QuitModel()
    program, thread, errors = _run_against_pty(model, b"abq")
    assert not thread.is_alive()
    assert program.final_model.keys[:2] == ["a", "b"]


def test_terminal_control_commands_against_tty():
    # Returning terminal-control commands from init exercises the real terminal
    # control paths (enter/exit alt screen, cursor, mouse, title) that are no-ops
    # in headless mode.
    from interrobang.command import (
        batch,
        clear_screen,
        enter_alt_screen,
        exit_alt_screen,
        hide_cursor,
        set_window_title,
        show_cursor,
    )

    class ControlModel:
        def init(self):
            return batch(
                enter_alt_screen,
                exit_alt_screen,
                hide_cursor,
                show_cursor,
                clear_screen,
                set_window_title("test"),
            )

        def update(self, msg):
            if isinstance(msg, KeyMsg) and msg.key == "q":
                return self, quit
            return self, None

        def view(self):
            return "x"

    program, thread, errors = _run_against_pty(ControlModel(), b"q", mouse=True)
    assert not thread.is_alive()
    assert errors == []
