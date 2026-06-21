"""A scrollable viewport over a block of text.

Set its content, give it a width and height, and forward messages so the user
can scroll with the arrow keys, Page Up/Down, Home/End, and the mouse wheel::

    vp = Viewport(width=60, height=20)
    vp.set_content(long_text)
    ...
    vp, cmd = vp.update(msg)
    print(vp.view())
"""

from __future__ import annotations

from .._ansi import truncate
from ..key import KeyMsg
from ..mouse import MouseButton, MouseMsg
from ..style import Style
from ..style.layout import pad_right

__all__ = ["Viewport"]


class Viewport:
    """A fixed-size scrollable window onto multi-line text."""

    def __init__(self, width: int = 80, height: int = 20):
        self.width = width
        self.height = height
        self.y_offset = 0
        self.style: Style = Style()
        self.mouse_wheel_delta = 3
        self._lines: list[str] = []

    # -- content -----------------------------------------------------------

    def set_content(self, text: str) -> None:
        """Replace the content; the scroll position is clamped to the new length."""
        self._lines = text.split("\n")
        self._clamp_offset()

    @property
    def total_lines(self) -> int:
        return len(self._lines)

    @property
    def visible_line_count(self) -> int:
        return min(self.height, len(self._lines))

    # -- scrolling ---------------------------------------------------------

    def _max_offset(self) -> int:
        return max(0, len(self._lines) - self.height)

    def _clamp_offset(self) -> None:
        self.y_offset = max(0, min(self.y_offset, self._max_offset()))

    def scroll_down(self, lines: int = 1) -> None:
        self.y_offset = min(self._max_offset(), self.y_offset + lines)

    def scroll_up(self, lines: int = 1) -> None:
        self.y_offset = max(0, self.y_offset - lines)

    def half_page_down(self) -> None:
        self.scroll_down(max(1, self.height // 2))

    def half_page_up(self) -> None:
        self.scroll_up(max(1, self.height // 2))

    def page_down(self) -> None:
        self.scroll_down(self.height)

    def page_up(self) -> None:
        self.scroll_up(self.height)

    def goto_top(self) -> None:
        self.y_offset = 0

    def goto_bottom(self) -> None:
        self.y_offset = self._max_offset()

    @property
    def at_top(self) -> bool:
        return self.y_offset <= 0

    @property
    def at_bottom(self) -> bool:
        return self.y_offset >= self._max_offset()

    def scroll_percent(self) -> float:
        """Fraction scrolled, from 0.0 (top) to 1.0 (bottom)."""
        max_offset = self._max_offset()
        if max_offset == 0:
            return 1.0
        return self.y_offset / max_offset

    # -- update ------------------------------------------------------------

    def update(self, msg: object) -> "tuple[Viewport, None]":
        """Handle scrolling keys and the mouse wheel."""
        if isinstance(msg, KeyMsg):
            key = msg.key
            if key in ("up", "k"):
                self.scroll_up()
            elif key in ("down", "j"):
                self.scroll_down()
            elif key in ("pgup", "b"):
                self.page_up()
            elif key in ("pgdown", "f", "space"):
                self.page_down()
            elif key in ("ctrl+u",):
                self.half_page_up()
            elif key in ("ctrl+d",):
                self.half_page_down()
            elif key in ("home", "g"):
                self.goto_top()
            elif key in ("end", "G"):
                self.goto_bottom()
        elif isinstance(msg, MouseMsg):
            if msg.button is MouseButton.WHEEL_UP:
                self.scroll_up(self.mouse_wheel_delta)
            elif msg.button is MouseButton.WHEEL_DOWN:
                self.scroll_down(self.mouse_wheel_delta)
        return self, None

    # -- view --------------------------------------------------------------

    def view(self) -> str:
        """Render the visible slice, padded to exactly ``width`` x ``height``."""
        visible = self._lines[self.y_offset : self.y_offset + self.height]
        rows: list[str] = []
        for line in visible:
            rows.append(pad_right(truncate(line, self.width), self.width))
        # Pad with blank lines so the viewport always fills its height.
        while len(rows) < self.height:
            rows.append(" " * self.width)
        return self.style.render("\n".join(rows))
