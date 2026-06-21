"""The :class:`Program` -- interrobang's event loop.

A program owns the lifecycle: it sets up the terminal, reads input on a
background thread, runs your ``update`` for each message, executes the commands
``update`` returns (timers, background work, terminal controls), and repaints
your ``view`` whenever the state changes. Call :meth:`Program.run` and it blocks
until your app quits, then returns the final model.

The whole loop also runs *headless* -- give it an in-memory input/output and
drive it with :meth:`Program.send` -- which is how the test suite exercises it
without a real terminal.
"""

from __future__ import annotations

import os
import queue
import signal
import threading
from typing import IO, Optional

from ._input import parse
from .command import (
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
)
from .key import KeyMsg
from .message import QuitMsg, WindowSizeMsg
from .model import Model
from .renderer import Renderer
from .style import Profile, set_color_profile, set_has_dark_background
from .terminal_io import Terminal

__all__ = ["Program", "run", "detect_profile", "detect_dark_background"]


def detect_profile(env: Optional[dict] = None, is_tty: bool = True) -> Profile:
    """Guess the terminal's color profile from the environment.

    Honors ``NO_COLOR`` (forces monochrome) and ``COLORTERM=truecolor``; falls
    back to inspecting ``TERM``. When output is not a TTY (piped to a file),
    color is disabled unless ``FORCE_COLOR`` or ``COLORTERM`` says otherwise.
    """
    env = os.environ if env is None else env
    if env.get("NO_COLOR"):
        return Profile.ASCII
    colorterm = env.get("COLORTERM", "").lower()
    forced = bool(env.get("FORCE_COLOR")) or colorterm != ""
    if not is_tty and not forced:
        return Profile.ASCII
    if "truecolor" in colorterm or "24bit" in colorterm:
        return Profile.TRUECOLOR
    term = env.get("TERM", "").lower()
    if "256color" in term:
        return Profile.ANSI256
    if term in ("", "dumb"):
        return Profile.ASCII if not forced else Profile.TRUECOLOR
    if "color" in term:
        return Profile.ANSI
    return Profile.ANSI256


def detect_dark_background(env: Optional[dict] = None) -> bool:
    """Best-effort guess at whether the terminal background is dark.

    Reads ``COLORFGBG`` (set by some terminals as ``"fg;bg"``); defaults to
    ``True`` because the overwhelming majority of terminals are dark.
    """
    env = os.environ if env is None else env
    fgbg = env.get("COLORFGBG", "")
    parts = fgbg.split(";")
    if len(parts) >= 2 and parts[-1].isdigit():
        bg = int(parts[-1])
        return bg <= 6 or bg == 8
    return True


class Program:
    """Runs a :class:`~interrobang.model.Model` to completion.

    Args:
        model: Your application model.
        alt_screen: Use the alternate screen buffer (best for full-screen apps).
        mouse: Enable mouse reporting.
        input: A binary input stream (defaults to stdin). Pass an in-memory
            stream to drive the program in tests.
        output: A text output stream (defaults to stdout).
        headless: Skip all terminal control (raw mode, cursor, signals). Implied
            when the output is not a real TTY.
        catch_interrupt: If true (the default), Ctrl+C quits the program instead
            of being delivered to ``update``.
    """

    def __init__(
        self,
        model: Model,
        *,
        alt_screen: bool = False,
        mouse: bool = False,
        input: IO | None = None,
        output: IO | None = None,
        headless: bool = False,
        catch_interrupt: bool = True,
    ):
        self.model = model
        self._alt_screen = alt_screen
        self._mouse = mouse
        self._catch_interrupt = catch_interrupt
        self._terminal = Terminal(input, output)
        self._input_provided = input is not None
        self._manage_tty = (not headless) and self._terminal.is_tty()
        self._has_input = self._input_provided or self._manage_tty

        self._queue: "queue.Queue" = queue.Queue()
        self._renderer: Renderer | None = None
        self._input_thread: threading.Thread | None = None
        self._running = False
        self._final_model = model
        self._error: BaseException | None = None
        self._prev_winch = None

    # -- public API --------------------------------------------------------

    def send(self, msg: object) -> None:
        """Enqueue a message from any thread."""
        self._queue.put(msg)

    def quit(self) -> None:
        """Ask the program to stop (enqueues a :class:`QuitMsg`)."""
        self.send(QuitMsg())

    @property
    def final_model(self) -> Model:
        """The model as of the last processed message (valid after :meth:`run`)."""
        return self._final_model

    def run(self) -> Model:
        """Run the event loop until the program quits; return the final model."""
        self._running = True
        self._final_model = self.model

        set_color_profile(detect_profile(is_tty=self._terminal.is_tty()))
        set_has_dark_background(detect_dark_background())
        self._renderer = Renderer(self._terminal, alt_screen=self._alt_screen)

        try:
            if self._manage_tty:
                self._terminal.make_raw()
                if self._alt_screen:
                    self._terminal.enter_alt_screen()
                self._terminal.hide_cursor()
                if self._mouse:
                    self._terminal.enable_mouse()
                self._install_signals()

            width, height = self._terminal.get_size()
            self._start_input()

            init = getattr(self.model, "init", None)
            if init is not None:
                self._dispatch(init())

            self.send(WindowSizeMsg(width, height))
            self._renderer.render(self.model.view())
            self._loop()
        finally:
            self._teardown()
        return self._final_model

    # -- main loop ---------------------------------------------------------

    def _loop(self) -> None:
        while self._running:
            msg = self._queue.get()
            if isinstance(msg, QuitMsg):
                break
            if self._catch_interrupt and isinstance(msg, KeyMsg) and msg.key == "ctrl+c":
                break
            if self._handle_control(msg):
                continue
            if isinstance(msg, WindowSizeMsg):
                self._renderer.reset()  # size changed: force a full repaint
            result = self.model.update(msg)
            if isinstance(result, tuple):
                self.model, cmd = result
            else:  # be lenient: a model alone means "no command"
                self.model, cmd = result, None
            self._final_model = self.model
            self._dispatch(cmd)
            self._renderer.render(self.model.view())

    def _handle_control(self, msg: object) -> bool:
        kind = type(msg)
        if kind is _EnterAltScreen:
            if self._manage_tty:
                self._terminal.enter_alt_screen()
            self._renderer.set_alt_screen(True)
            self._renderer.render(self.model.view())
        elif kind is _ExitAltScreen:
            if self._manage_tty:
                self._terminal.exit_alt_screen()
            self._renderer.set_alt_screen(False)
            self._renderer.render(self.model.view())
        elif kind is _HideCursor:
            if self._manage_tty:
                self._terminal.hide_cursor()
        elif kind is _ShowCursor:
            if self._manage_tty:
                self._terminal.show_cursor()
        elif kind is _EnableMouse:
            if self._manage_tty:
                self._terminal.enable_mouse()
        elif kind is _DisableMouse:
            if self._manage_tty:
                self._terminal.disable_mouse()
        elif kind is _ClearScreen:
            self._renderer.reset()
            if self._manage_tty:
                self._terminal.clear()
            self._renderer.render(self.model.view())
        elif kind is _SetWindowTitle:
            if self._manage_tty:
                self._terminal.set_title(msg.title)
        else:
            return False
        return True

    # -- commands ----------------------------------------------------------

    def _dispatch(self, cmd: object) -> None:
        if cmd is None:
            return
        if isinstance(cmd, BatchCmd):
            for child in cmd.cmds:
                self._dispatch(child)
            return
        if isinstance(cmd, SequenceCmd):
            threading.Thread(target=self._run_sequence, args=(cmd.cmds,), daemon=True).start()
            return
        threading.Thread(target=self._run_cmd, args=(cmd,), daemon=True).start()

    def _run_cmd(self, cmd) -> None:
        try:
            msg = cmd()
        except BaseException as exc:  # noqa: BLE001 - surfaced after teardown
            self._on_cmd_error(exc)
            return
        if msg is not None:
            self.send(msg)

    def _run_sequence(self, cmds) -> None:
        for child in cmds:
            if child is None:
                continue
            try:
                if isinstance(child, SequenceCmd):
                    self._run_sequence(child.cmds)
                elif isinstance(child, BatchCmd):
                    for c in child.cmds:
                        self._run_cmd_sync(c)
                else:
                    self._run_cmd_sync(child)
            except BaseException as exc:  # noqa: BLE001
                self._on_cmd_error(exc)
                return

    def _run_cmd_sync(self, cmd) -> None:
        msg = cmd()
        if msg is not None:
            self.send(msg)

    def _on_cmd_error(self, exc: BaseException) -> None:
        if self._error is None:
            self._error = exc
            self.send(QuitMsg())

    # -- input -------------------------------------------------------------

    def _start_input(self) -> None:
        if not self._has_input:
            return
        self._input_thread = threading.Thread(target=self._input_loop, daemon=True)
        self._input_thread.start()

    def _input_loop(self) -> None:
        buffer = b""
        while self._running:
            data = self._terminal.read_bytes(timeout=0.05)
            if data is None:  # end of input
                if buffer:
                    events, buffer = parse(buffer, flush=True)
                    for event in events:
                        self.send(event)
                return
            if data == b"":  # idle: flush any dangling ESC
                if buffer:
                    events, buffer = parse(buffer, flush=True)
                    for event in events:
                        self.send(event)
                continue
            buffer += data
            events, buffer = parse(buffer)
            for event in events:
                self.send(event)

    # -- signals -----------------------------------------------------------

    def _install_signals(self) -> None:
        if not hasattr(signal, "SIGWINCH"):
            return
        try:
            self._prev_winch = signal.signal(signal.SIGWINCH, self._on_winch)
        except (ValueError, OSError):
            self._prev_winch = None  # not on the main thread; resize won't fire

    def _uninstall_signals(self) -> None:
        if self._prev_winch is not None and hasattr(signal, "SIGWINCH"):
            try:
                signal.signal(signal.SIGWINCH, self._prev_winch)
            except (ValueError, OSError):
                pass
            self._prev_winch = None

    def _on_winch(self, signum, frame) -> None:
        width, height = self._terminal.get_size()
        self.send(WindowSizeMsg(width, height))

    # -- teardown ----------------------------------------------------------

    def _teardown(self) -> None:
        self._running = False
        if self._manage_tty:
            if self._mouse:
                self._terminal.disable_mouse()
            self._terminal.show_cursor()
            if self._renderer is not None and self._renderer.alt_screen:
                self._terminal.exit_alt_screen()
            self._terminal.restore()
            self._uninstall_signals()
        if self._renderer is not None and not self._renderer.alt_screen:
            self._renderer.finish()
        self._terminal.flush()
        if self._error is not None:
            err = self._error
            self._error = None
            raise err


def run(model: Model, **kwargs) -> Model:
    """Convenience wrapper: ``run(model)`` is ``Program(model).run()``."""
    return Program(model, **kwargs).run()
