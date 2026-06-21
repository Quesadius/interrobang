"""The real terminal: raw mode, the alternate screen, mouse, and byte I/O.

This is the one corner of interrobang that genuinely talks to a TTY, so it is
kept small and isolated. The rest of the library (parsing, rendering, the event
loop) works on plain strings and bytes and can be tested without a terminal;
this module is what those pieces drive at runtime.

It targets POSIX terminals (macOS and Linux). On platforms or streams without a
real TTY it degrades to plain reads/writes so headless and piped use still work.
"""

from __future__ import annotations

import os
import sys
from typing import IO, Optional

# ANSI control sequences used to drive the terminal.
_ALT_SCREEN_ON = "\x1b[?1049h"
_ALT_SCREEN_OFF = "\x1b[?1049l"
_HIDE_CURSOR = "\x1b[?25l"
_SHOW_CURSOR = "\x1b[?25h"
_MOUSE_ON = "\x1b[?1000h\x1b[?1002h\x1b[?1006h"
_MOUSE_OFF = "\x1b[?1006l\x1b[?1002l\x1b[?1000l"
_CLEAR = "\x1b[2J\x1b[H"


def _fileno(stream: IO) -> Optional[int]:
    try:
        fd = stream.fileno()
        return fd if isinstance(fd, int) and fd >= 0 else None
    except Exception:
        return None


class Terminal:
    """Owns a terminal's raw-mode state and provides byte-level read/write."""

    def __init__(self, input_stream: IO | None = None, output_stream: IO | None = None):
        self.input = input_stream if input_stream is not None else sys.stdin
        self.output = output_stream if output_stream is not None else sys.stdout
        self._in_fd = _fileno(self.input)
        self._out_fd = _fileno(self.output)
        self._old_settings = None
        self._raw = False
        self._alt = False
        self._mouse = False
        self._cursor_hidden = False

    # -- capabilities ------------------------------------------------------

    def is_tty(self) -> bool:
        """True only if both ends are real terminals."""
        try:
            return bool(self.input.isatty() and self.output.isatty())
        except Exception:
            return False

    def get_size(self) -> tuple[int, int]:
        """Return the terminal size as ``(columns, rows)``, with a sane default."""
        for fd in (self._out_fd, self._in_fd):
            if fd is not None:
                try:
                    size = os.get_terminal_size(fd)
                    return size.columns, size.lines
                except OSError:
                    continue
        return 80, 24

    # -- raw mode ----------------------------------------------------------

    def make_raw(self) -> None:
        """Put the terminal into raw mode (no echo, no line buffering)."""
        if self._in_fd is None or not self.is_tty():
            return
        import termios
        import tty

        self._old_settings = termios.tcgetattr(self._in_fd)
        tty.setraw(self._in_fd)
        self._raw = True

    def restore(self) -> None:
        """Restore the terminal settings saved by :meth:`make_raw`."""
        if self._old_settings is not None and self._in_fd is not None:
            import termios

            termios.tcsetattr(self._in_fd, termios.TCSADRAIN, self._old_settings)
            self._old_settings = None
            self._raw = False

    # -- writing -----------------------------------------------------------

    def write(self, text: str) -> None:
        try:
            self.output.write(text)
        except (BrokenPipeError, ValueError):
            pass

    def flush(self) -> None:
        try:
            self.output.flush()
        except (BrokenPipeError, ValueError):
            pass

    # -- screen / cursor / mouse control ----------------------------------

    def enter_alt_screen(self) -> None:
        if not self._alt:
            self.write(_ALT_SCREEN_ON)
            self.write(_CLEAR)
            self._alt = True

    def exit_alt_screen(self) -> None:
        if self._alt:
            self.write(_ALT_SCREEN_OFF)
            self._alt = False

    def hide_cursor(self) -> None:
        if not self._cursor_hidden:
            self.write(_HIDE_CURSOR)
            self._cursor_hidden = True

    def show_cursor(self) -> None:
        if self._cursor_hidden:
            self.write(_SHOW_CURSOR)
            self._cursor_hidden = False

    def enable_mouse(self) -> None:
        if not self._mouse:
            self.write(_MOUSE_ON)
            self._mouse = True

    def disable_mouse(self) -> None:
        if self._mouse:
            self.write(_MOUSE_OFF)
            self._mouse = False

    def clear(self) -> None:
        self.write(_CLEAR)

    def set_title(self, title: str) -> None:
        self.write(f"\x1b]0;{title}\x07")

    @property
    def in_alt_screen(self) -> bool:
        return self._alt

    # -- reading -----------------------------------------------------------

    def read_bytes(self, timeout: float | None) -> Optional[bytes]:
        """Read available input bytes.

        Returns the bytes read, ``b""`` if *timeout* elapsed with no input, or
        ``None`` at end of input. When the input stream supports ``select`` (a
        real TTY or pipe) this waits up to *timeout* seconds; otherwise it falls
        back to a plain blocking read.
        """
        if self._in_fd is not None:
            import select

            try:
                ready, _, _ = select.select([self._in_fd], [], [], timeout)
            except (OSError, ValueError):
                return None
            if not ready:
                return b""
            try:
                data = os.read(self._in_fd, 1024)
            except OSError:
                return None
            return data if data else None

        # No selectable fd (e.g. an in-memory stream): blocking read.
        try:
            data = self.input.read(1024)
        except Exception:
            return None
        if data is None:
            return b""
        if isinstance(data, str):
            data = data.encode("utf-8", "replace")
        return data if data else None
