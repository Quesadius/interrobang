"""A scrollable table with row selection. Run: python examples/table.py."""

import interrobang as irb
from interrobang import KeyMsg, quit
from interrobang.components import Column, Table
from interrobang.style import Color, Style

ROWS = [
    ["bubbletea", "Go", "Charm", "29k"],
    ["lipgloss", "Go", "Charm", "9k"],
    ["rich", "Python", "Textualize", "49k"],
    ["textual", "Python", "Textualize", "27k"],
    ["interrobang", "Python", "you", "1"],
    ["blessed", "Python", "jquast", "3k"],
    ["urwid", "Python", "urwid", "3k"],
    ["prompt_toolkit", "Python", "jonathanslenders", "9k"],
    ["ratatui", "Rust", "ratatui-org", "11k"],
    ["ink", "JS", "vadimdemedes", "27k"],
]


class Model:
    def __init__(self):
        self.table = Table(
            columns=[
                Column("Library", 16),
                Column("Language", 10),
                Column("Author", 18),
                Column("Stars", 6),
            ],
            rows=ROWS,
            height=12,
        )

    def init(self):
        return None

    def update(self, msg):
        if isinstance(msg, KeyMsg) and msg.key in ("q", "ctrl+c", "esc"):
            return self, quit
        self.table, cmd = self.table.update(msg)
        return self, cmd

    def view(self):
        title = Style().bold().foreground(Color("#7D56F4")).render("TUI libraries")
        row = self.table.selected_row()
        selected = Style().faint().render(f"selected: {row[0] if row else '-'}")
        hint = Style().faint().render("↑/↓ move · q quit")
        return f"\n{title}\n\n{self.table.view()}\n\n{selected}\n{hint}\n"


if __name__ == "__main__":
    from _shared import run_example

    run_example(Model())
