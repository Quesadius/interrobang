"""A scrollable, selectable, filterable list.

Feed it items (any object exposing ``title`` and ``description``, or use the
provided :class:`Item`), and it handles cursor movement, paging, and an
optional fuzzy-ish substring filter you toggle with ``/``::

    items = [Item("Interrobang", "asks and exclaims"), Item("Ellipsis", "a trailing off")]
    lst = List(items, width=40, height=12)
    lst.title = "Punctuation"
    ...
    lst, cmd = lst.update(msg)
    print(lst.view())

The currently highlighted item is :meth:`List.selected_item`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..key import KeyMsg, KeyType
from ..style import Color, Style
from ..theme import Theme, get_theme, register_themed

__all__ = ["Item", "List"]


@dataclass
class Item:
    """A simple list item with a title and optional description."""

    title: str
    description: str = ""


def _title_of(item: Any) -> str:
    title = getattr(item, "title", item)
    return title() if callable(title) else str(title)


def _desc_of(item: Any) -> str:
    desc = getattr(item, "description", "")
    return desc() if callable(desc) else str(desc)


class List:
    """A vertical list with selection, paging, and filtering."""

    def __init__(self, items: list | None = None, width: int = 40, height: int = 14):
        self.items: list = list(items) if items else []
        self.width = width
        self.height = height
        self.cursor = 0
        self.offset = 0
        self.title = ""
        self.show_description = True
        self.show_status_bar = True

        # Filtering.
        self.filter_enabled = True
        self.filtering = False
        self.filter_text = ""

        # Styles (defaults come from the active theme).
        self.normal_style = Style()
        self.cursor_prefix = "> "
        self.normal_prefix = "  "
        self.title_style = Style()
        self.selected_style = Style()
        self.description_style = Style()
        self.status_style = Style()
        register_themed(self)
        self._apply_theme(get_theme())

    def _apply_theme(self, theme: Theme) -> None:
        self.title_style = Style().bold().foreground(theme.on_primary).background(theme.primary).padding(0, 1)
        self.selected_style = Style().foreground(theme.selection).bold()
        self.description_style = Style().foreground(theme.muted)
        self.status_style = Style().foreground(theme.muted)

    # -- data --------------------------------------------------------------

    def set_items(self, items: list) -> None:
        self.items = list(items)
        self.cursor = 0
        self.offset = 0

    def visible_items(self) -> list:
        """Items after applying the current filter."""
        if not self.filter_text:
            return self.items
        needle = self.filter_text.lower()
        return [it for it in self.items if needle in _title_of(it).lower()]

    def selected_item(self) -> Any | None:
        """The highlighted item, or ``None`` if the list is empty."""
        items = self.visible_items()
        if not items or self.cursor >= len(items):
            return None
        return items[self.cursor]

    # -- navigation --------------------------------------------------------

    def _rows_per_page(self) -> int:
        rows = self.height
        if self.title:
            rows -= 1
        if self.show_status_bar:
            rows -= 1
        per_item = 2 if self.show_description else 1
        return max(1, rows // per_item)

    def cursor_up(self) -> None:
        if self.cursor > 0:
            self.cursor -= 1
            if self.cursor < self.offset:
                self.offset = self.cursor

    def cursor_down(self) -> None:
        count = len(self.visible_items())
        if self.cursor < count - 1:
            self.cursor += 1
            page = self._rows_per_page()
            if self.cursor >= self.offset + page:
                self.offset = self.cursor - page + 1

    # -- update ------------------------------------------------------------

    def update(self, msg: object) -> "tuple[List, None]":
        if not isinstance(msg, KeyMsg):
            return self, None

        if self.filtering:
            return self._update_filtering(msg)

        key = msg.key
        if key in ("up", "k"):
            self.cursor_up()
        elif key in ("down", "j"):
            self.cursor_down()
        elif key in ("home", "g"):
            self.cursor = 0
            self.offset = 0
        elif key in ("end", "G"):
            self.cursor = max(0, len(self.visible_items()) - 1)
            self._reclamp_offset()
        elif key == "/" and self.filter_enabled:
            self.filtering = True
            self.filter_text = ""
            self.cursor = 0
            self.offset = 0
        return self, None

    def _update_filtering(self, msg: KeyMsg) -> "tuple[List, None]":
        key = msg.key
        if key in ("enter", "esc"):
            self.filtering = False
            if key == "esc":
                self.filter_text = ""
        elif key == "backspace":
            self.filter_text = self.filter_text[:-1]
            self.cursor = 0
            self.offset = 0
        elif msg.type is KeyType.RUNES and not msg.ctrl and not msg.alt:
            self.filter_text += msg.runes
            self.cursor = 0
            self.offset = 0
        elif msg.type is KeyType.SPACE:
            self.filter_text += " "
        return self, None

    def _reclamp_offset(self) -> None:
        page = self._rows_per_page()
        if self.cursor >= self.offset + page:
            self.offset = max(0, self.cursor - page + 1)

    # -- view --------------------------------------------------------------

    def view(self) -> str:
        lines: list[str] = []
        if self.title:
            lines.append(self.title_style.render(self.title))

        items = self.visible_items()
        page = self._rows_per_page()
        window = items[self.offset : self.offset + page]

        if not window:
            lines.append(self.description_style.render("  (no items)"))
        for i, item in enumerate(window):
            index = self.offset + i
            selected = index == self.cursor
            prefix = self.cursor_prefix if selected else self.normal_prefix
            title_style = self.selected_style if selected else self.normal_style
            lines.append(prefix + title_style.render(_title_of(item)))
            if self.show_description:
                desc = _desc_of(item)
                lines.append(self.normal_prefix + self.description_style.render(desc))

        if self.show_status_bar:
            lines.append(self._status_bar(len(items)))
        return "\n".join(lines)

    def _status_bar(self, count: int) -> str:
        if self.filtering:
            return self.status_style.render(f"/{self.filter_text}")
        if self.filter_text:
            return self.status_style.render(f"{count} items · filter: {self.filter_text}")
        position = f"{self.cursor + 1}/{count}" if count else "0/0"
        return self.status_style.render(f"{count} items · {position}")
