"""Turn a view string into the escape sequences that paint it on screen.

The renderer keeps the previous frame so it can skip redundant repaints and,
in inline mode, redraw only its own block of lines without disturbing the rest
of the scrollback. It writes through any object exposing ``write``/``flush``
(the real :class:`~interrobang.terminal_io.Terminal`, or a buffer in tests).
"""

from __future__ import annotations

from typing import Protocol


class Writer(Protocol):
    def write(self, text: str) -> None: ...
    def flush(self) -> None: ...


class Renderer:
    """Repaints frames efficiently in either inline or alt-screen mode."""

    def __init__(self, writer: Writer, alt_screen: bool = False):
        self._writer = writer
        self._alt_screen = alt_screen
        self._last_frame: str | None = None
        self._last_line_count = 0

    @property
    def alt_screen(self) -> bool:
        return self._alt_screen

    def set_alt_screen(self, enabled: bool) -> None:
        """Switch rendering mode; the next render performs a full repaint."""
        if enabled != self._alt_screen:
            self._alt_screen = enabled
            self.reset()

    def reset(self) -> None:
        """Forget the previous frame so the next render repaints from scratch."""
        self._last_frame = None
        self._last_line_count = 0

    def render(self, frame: str) -> None:
        """Paint *frame*, skipping the write entirely if it is unchanged."""
        if frame == self._last_frame:
            return
        lines = frame.split("\n")
        if self._alt_screen:
            self._render_alt(lines)
        else:
            self._render_inline(lines)
        self._writer.flush()
        self._last_frame = frame
        self._last_line_count = len(lines)

    def _render_alt(self, lines: list[str]) -> None:
        # Home the cursor, draw each line clearing to its end, then clear any
        # rows left over from a taller previous frame.
        body = "\x1b[H" + "\r\n".join(line + "\x1b[K" for line in lines) + "\x1b[J"
        self._writer.write(body)

    def _render_inline(self, lines: list[str]) -> None:
        out: list[str] = []
        if self._last_line_count > 0:
            out.append("\r")
            if self._last_line_count > 1:
                out.append(f"\x1b[{self._last_line_count - 1}A")
        count = len(lines)
        for i, line in enumerate(lines):
            out.append("\x1b[2K")  # clear the whole line
            out.append(line)
            if i < count - 1:
                out.append("\r\n")
        # If this frame is shorter, wipe the now-stale trailing lines.
        if self._last_line_count > count:
            extra = self._last_line_count - count
            out.append("\r\n\x1b[2K" * extra)
            out.append(f"\x1b[{extra}A")
        self._writer.write("".join(out))

    def finish(self) -> None:
        """Move the cursor below the final inline frame (no-op in alt screen)."""
        if not self._alt_screen and self._last_line_count > 0:
            self._writer.write("\r\n")
            self._writer.flush()
