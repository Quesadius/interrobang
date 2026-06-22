"""A horizontal progress bar, with optional color gradient.

The bar is stateless to render -- give it a percentage in ``[0, 1]``::

    bar = Progress(width=40).with_gradient("#FF7CCB", "#FDFF8C")
    print(bar.view_as(0.62))

Or store the percentage on the component and animate it from ``update``.
"""

from __future__ import annotations

from .._ansi import string_width
from ..style import Color, Style, parse_hex
from ..theme import get_theme

__all__ = ["Progress"]


def _clamp(value: float) -> float:
    return 0.0 if value < 0 else 1.0 if value > 1 else value


def _lerp(a: int, b: int, t: float) -> int:
    return round(a + (b - a) * t)


class Progress:
    """A progress bar that fills from left to right."""

    def __init__(self, width: int = 40):
        theme = get_theme()
        self.width = width
        self.percent: float = 0.0
        self.full_char: str = "█"
        self.empty_char: str = "░"
        self.show_percentage: bool = True
        self.percent_style: Style = Style().foreground(theme.muted)
        self.empty_style: Style = Style().foreground(theme.muted)
        self._solid: Color | None = None
        # By default the bar fills with the theme's gradient.
        self._gradient: tuple[tuple[int, int, int], tuple[int, int, int]] | None = (
            parse_hex(theme.gradient_start),
            parse_hex(theme.gradient_end),
        )

    # -- configuration -----------------------------------------------------

    def with_solid(self, color: str) -> "Progress":
        """Fill the bar with a single solid color (chainable)."""
        self._solid = Color(color)
        self._gradient = None
        return self

    def with_gradient(self, start: str, end: str) -> "Progress":
        """Fill the bar with a left-to-right color gradient (chainable)."""
        self._gradient = (parse_hex(start), parse_hex(end))
        self._solid = None
        return self

    # -- state -------------------------------------------------------------

    def set_percent(self, percent: float) -> None:
        """Set the stored percentage (clamped to ``[0, 1]``)."""
        self.percent = _clamp(percent)

    def incr_percent(self, delta: float) -> None:
        """Adjust the stored percentage by *delta*, clamped to ``[0, 1]``."""
        self.percent = _clamp(self.percent + delta)

    # -- view --------------------------------------------------------------

    def view(self) -> str:
        """Render the bar at the stored percentage."""
        return self.view_as(self.percent)

    def view_as(self, percent: float) -> str:
        """Render the bar at an explicit *percent* in ``[0, 1]``."""
        percent = _clamp(percent)
        suffix = f" {int(round(percent * 100))}%" if self.show_percentage else ""
        bar_width = max(0, self.width - string_width(suffix))
        filled = int(round(bar_width * percent))
        empty = bar_width - filled

        if self._gradient is not None:
            fill = self._render_gradient(filled, bar_width)
        else:
            color = self._solid or Color("#7D56F4")
            fill = Style().foreground(color).render(self.full_char * filled)

        rest = self.empty_style.render(self.empty_char * empty)
        tail = self.percent_style.render(suffix) if suffix else ""
        return fill + rest + tail

    def _render_gradient(self, filled: int, bar_width: int) -> str:
        assert self._gradient is not None
        (r1, g1, b1), (r2, g2, b2) = self._gradient
        cells: list[str] = []
        denom = max(1, bar_width - 1)
        for i in range(filled):
            t = i / denom
            color = Color.from_rgb(_lerp(r1, r2, t), _lerp(g1, g2, t), _lerp(b1, b2, t))
            cells.append(Style().foreground(color).render(self.full_char))
        return "".join(cells)
