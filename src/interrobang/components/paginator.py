"""Pagination logic and a compact page indicator.

Handles the arithmetic of splitting N items across pages and renders either a
row of dots (●○○) or an ``N/M`` counter::

    p = Paginator(per_page=10)
    p.set_total_items(95)        # -> 10 pages
    start, end = p.slice_bounds()  # indices into your list for the current page
    print(p.view())              # ● ○ ○ ○ ○ ○ ○ ○ ○ ○
"""

from __future__ import annotations

from enum import Enum, auto

from ..key import KeyMsg
from ..style import Style
from ..theme import get_theme

__all__ = ["PaginatorType", "Paginator"]


class PaginatorType(Enum):
    """How the paginator renders itself."""

    DOTS = auto()  #: A row of filled/empty dots.
    ARABIC = auto()  #: A ``page/total`` counter.


class Paginator:
    """Tracks the current page and computes per-page slices."""

    def __init__(self, per_page: int = 10, page: int = 0):
        self.per_page = max(1, per_page)
        self.page = page
        self.total_pages = 1
        self.type = PaginatorType.DOTS
        self.active_dot = "●"
        self.inactive_dot = "○"
        theme = get_theme()
        self.active_style = Style().foreground(theme.primary)
        self.inactive_style = Style().foreground(theme.muted)

    def set_total_items(self, total: int) -> int:
        """Recompute :attr:`total_pages` for *total* items; returns the page count."""
        self.total_pages = max(1, -(-total // self.per_page))  # ceil division
        if self.page > self.total_pages - 1:
            self.page = self.total_pages - 1
        return self.total_pages

    def items_on_page(self, total_items: int) -> int:
        """How many items appear on the current page given *total_items*."""
        if total_items <= 0:
            return 0
        start = self.page * self.per_page
        return max(0, min(self.per_page, total_items - start))

    def slice_bounds(self, total_items: int | None = None) -> tuple[int, int]:
        """Return ``(start, end)`` indices for slicing the current page's items."""
        start = self.page * self.per_page
        end = start + self.per_page
        if total_items is not None:
            end = min(end, total_items)
        return start, end

    @property
    def on_first_page(self) -> bool:
        return self.page <= 0

    @property
    def on_last_page(self) -> bool:
        return self.page >= self.total_pages - 1

    def next_page(self) -> None:
        if not self.on_last_page:
            self.page += 1

    def prev_page(self) -> None:
        if not self.on_first_page:
            self.page -= 1

    def update(self, msg: object) -> "tuple[Paginator, None]":
        """Move between pages with left/right (or h/l)."""
        if isinstance(msg, KeyMsg):
            if msg.key in ("left", "h", "pgup"):
                self.prev_page()
            elif msg.key in ("right", "l", "pgdown"):
                self.next_page()
        return self, None

    def view(self) -> str:
        """Render the page indicator."""
        if self.type is PaginatorType.ARABIC:
            return f"{self.page + 1}/{self.total_pages}"
        dots = [
            self.active_style.render(self.active_dot)
            if i == self.page
            else self.inactive_style.render(self.inactive_dot)
            for i in range(self.total_pages)
        ]
        return " ".join(dots)
