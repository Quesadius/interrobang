"""Commands -- how ``update`` asks the runtime to *do* something.

``update`` must stay pure: it computes the next state and, if it wants a side
effect (quit, start a timer, fetch a URL, write a file), it returns a *command*
describing that effect instead of performing it. The runtime runs the command,
usually on a background thread, and feeds whatever message it produces back into
``update``. This keeps your state transitions deterministic and testable.

A command is simply a zero-argument callable that returns a message (or
``None``). The helpers here cover the common cases:

* :data:`quit` -- stop the program.
* :func:`batch` -- run several commands concurrently.
* :func:`sequence` -- run several commands one after another.
* :func:`tick` / :func:`every` -- timers.
* terminal controls -- :func:`enter_alt_screen`, :func:`enable_mouse`, ...
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Callable, Optional, Union

from .message import Msg, QuitMsg

__all__ = [
    "Cmd",
    "Command",
    "quit",
    "batch",
    "sequence",
    "tick",
    "every",
    "enter_alt_screen",
    "exit_alt_screen",
    "hide_cursor",
    "show_cursor",
    "enable_mouse",
    "disable_mouse",
    "clear_screen",
    "set_window_title",
    "BatchCmd",
    "SequenceCmd",
]

#: A command: a zero-argument callable returning a message (or ``None``).
Cmd = Callable[[], Optional[Msg]]


@dataclass(frozen=True)
class BatchCmd:
    """Marker telling the runtime to run several commands concurrently."""

    cmds: tuple


@dataclass(frozen=True)
class SequenceCmd:
    """Marker telling the runtime to run several commands strictly in order."""

    cmds: tuple


#: Anything ``update`` may return as its command slot.
Command = Union[Cmd, BatchCmd, SequenceCmd, None]


def quit() -> QuitMsg:
    """A command that shuts the program down.

    Return it from ``update`` like any other command::

        if msg.key == "q":
            return self, quit
    """
    return QuitMsg()


def batch(*cmds: Command) -> Command:
    """Combine commands to run **concurrently**; results arrive as they finish.

    ``None`` entries are dropped. Returns ``None`` if nothing is left and the
    single command unchanged if only one survives.
    """
    real = [c for c in cmds if c is not None]
    if not real:
        return None
    if len(real) == 1:
        return real[0]
    return BatchCmd(tuple(real))


def sequence(*cmds: Command) -> Command:
    """Combine commands to run **in order**, each finishing before the next starts."""
    real = [c for c in cmds if c is not None]
    if not real:
        return None
    if len(real) == 1:
        return real[0]
    return SequenceCmd(tuple(real))


def tick(seconds: float, fn: Callable[[float], Msg]) -> Cmd:
    """A command that waits *seconds* then calls ``fn(now)`` to make a message.

    ``now`` is the current wall-clock time (``time.time()``). Tickers do not
    repeat on their own; re-issue the command from ``update`` to keep ticking::

        def update(self, msg):
            if isinstance(msg, TickMsg):
                return self, tick(1.0, lambda t: TickMsg(t))
    """

    def cmd() -> Msg:
        time.sleep(max(0.0, seconds))
        return fn(time.time())

    return cmd


def every(seconds: float, fn: Callable[[float], Msg]) -> Cmd:
    """Like :func:`tick`, but aligned to the wall clock.

    The wait ends at the next multiple of *seconds* since the epoch, so repeated
    ``every`` ticks stay on a steady cadence even if processing takes a moment.
    """

    def cmd() -> Msg:
        now = time.time()
        target = (math.floor(now / seconds) + 1) * seconds
        time.sleep(max(0.0, target - now))
        return fn(time.time())

    return cmd


# --- terminal control commands ------------------------------------------
# Each returns a small internal message the Program loop intercepts; they are
# never passed to your update method.


@dataclass(frozen=True)
class _EnterAltScreen:
    pass


@dataclass(frozen=True)
class _ExitAltScreen:
    pass


@dataclass(frozen=True)
class _HideCursor:
    pass


@dataclass(frozen=True)
class _ShowCursor:
    pass


@dataclass(frozen=True)
class _EnableMouse:
    pass


@dataclass(frozen=True)
class _DisableMouse:
    pass


@dataclass(frozen=True)
class _ClearScreen:
    pass


@dataclass(frozen=True)
class _SetWindowTitle:
    title: str


def enter_alt_screen() -> Msg:
    """A command that switches to the alternate screen buffer (full-screen apps)."""
    return _EnterAltScreen()


def exit_alt_screen() -> Msg:
    """A command that switches back to the normal screen buffer."""
    return _ExitAltScreen()


def hide_cursor() -> Msg:
    """A command that hides the terminal cursor."""
    return _HideCursor()


def show_cursor() -> Msg:
    """A command that shows the terminal cursor."""
    return _ShowCursor()


def enable_mouse() -> Msg:
    """A command that enables mouse reporting (SGR mode)."""
    return _EnableMouse()


def disable_mouse() -> Msg:
    """A command that disables mouse reporting."""
    return _DisableMouse()


def clear_screen() -> Msg:
    """A command that clears the screen on the next render."""
    return _ClearScreen()


def set_window_title(title: str) -> Cmd:
    """A command that sets the terminal window title."""

    def cmd() -> Msg:
        return _SetWindowTitle(title)

    return cmd
