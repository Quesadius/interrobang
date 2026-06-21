"""A scrollable table with a header, fixed-width columns, and row selection.

Define columns, set rows, and forward messages for up/down navigation::

    table = Table(
        columns=[Column("Name", 20), Column("Language", 12), Column("Stars", 8)],
        rows=[["bubbletea", "Go", "25k"], ["interrobang", "Python", "1"]],
        height=10,
    )
    table, cmd = table.update(msg)
    print(table.view())

The highlighted row is :meth:`Table.selected_row`.
"""

from __future__ import annotations

from dataclasses import dataclass

from .._ansi import truncate
from ..key import KeyMsg
from ..style import Color, Style
from ..style.layout import pad_right

__all__ = ["Column", "Table"]


@dataclass
class Column:
    """A table column: a header title and a fixed cell width (in cells)."""

    title: str
    width: int


class Table:
    """A grid of string cells with a selectable, scrollable body."""

    def __init__(
        self,
        columns: list[Column] | None = None,
        rows: list[list[str]] | None = None,
        height: int = 10,
    ):
        self.columns: list[Column] = columns or []
        self.rows: list[list[str]] = rows or []
        self.height = height
        self.cursor = 0
        self.offset = 0
        self.focused = True
        self.column_gap = 1

        self.header_style = Style().bold().foreground(Color("#FAFAFA"))
        self.selected_style = Style().foreground(Color("#1A1A1A")).background(Color("#EE6FF8"))
        self.cell_style = Style()

    # -- data --------------------------------------------------------------

    def set_rows(self, rows: list[list[str]]) -> None:
        self.rows = rows
        self.cursor = 0
        self.offset = 0

    def selected_row(self) -> list[str] | None:
        """The highlighted row, or ``None`` if the table is empty."""
        if not self.rows or self.cursor >= len(self.rows):
            return None
        return self.rows[self.cursor]

    # -- navigation --------------------------------------------------------

    def _body_height(self) -> int:
        # Two lines go to the header and its underline.
        return max(1, self.height - 2)

    def cursor_up(self) -> None:
        if self.cursor > 0:
            self.cursor -= 1
            if self.cursor < self.offset:
                self.offset = self.cursor

    def cursor_down(self) -> None:
        if self.cursor < len(self.rows) - 1:
            self.cursor += 1
            page = self._body_height()
            if self.cursor >= self.offset + page:
                self.offset = self.cursor - page + 1

    def goto_top(self) -> None:
        self.cursor = 0
        self.offset = 0

    def goto_bottom(self) -> None:
        self.cursor = max(0, len(self.rows) - 1)
        page = self._body_height()
        self.offset = max(0, self.cursor - page + 1)

    def update(self, msg: object) -> "tuple[Table, None]":
        if self.focused and isinstance(msg, KeyMsg):
            key = msg.key
            if key in ("up", "k"):
                self.cursor_up()
            elif key in ("down", "j"):
                self.cursor_down()
            elif key in ("home", "g"):
                self.goto_top()
            elif key in ("end", "G"):
                self.goto_bottom()
        return self, None

    # -- view --------------------------------------------------------------

    def _format_cells(self, cells: list[str]) -> list[str]:
        out: list[str] = []
        for i, col in enumerate(self.columns):
            value = cells[i] if i < len(cells) else ""
            out.append(pad_right(truncate(value, col.width), col.width))
        return out

    def _row_text(self, cells: list[str]) -> str:
        gap = " " * self.column_gap
        return gap.join(self._format_cells(cells))

    def view(self) -> str:
        lines: list[str] = []
        header_cells = [col.title for col in self.columns]
        lines.append(self.header_style.render(self._row_text(header_cells)))

        total_width = sum(col.width for col in self.columns)
        total_width += self.column_gap * max(0, len(self.columns) - 1)
        lines.append("─" * total_width)

        page = self._body_height()
        window = self.rows[self.offset : self.offset + page]
        for i, row in enumerate(window):
            index = self.offset + i
            text = self._row_text(row)
            if index == self.cursor and self.focused:
                lines.append(self.selected_style.render(pad_right(text, total_width)))
            else:
                lines.append(self.cell_style.render(text))
        return "\n".join(lines)
