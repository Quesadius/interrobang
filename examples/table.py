"""A scrollable table with row selection. Run: python examples/table.py."""

import interrobang as irb
from interrobang import KeyMsg, get_theme, quit
from interrobang.components import Column, Table
from interrobang.style import Style

ROWS = [
    ["‽", "Interrobang", "U+203D", "1962"],
    ["!", "Exclamation point", "U+0021", "1400s"],
    ["?", "Question mark", "U+003F", "1500s"],
    ["—", "Em dash", "U+2014", "—"],
    ["…", "Ellipsis", "U+2026", "—"],
    ["&", "Ampersand", "U+0026", "~50 BC"],
    [";", "Semicolon", "U+003B", "1494"],
    [":", "Colon", "U+003A", "1500s"],
    ["¶", "Pilcrow", "U+00B6", "1100s"],
    ["*", "Asterisk", "U+002A", "~200 BC"],
]


class Model:
    def __init__(self):
        self.table = Table(
            columns=[
                Column("Mark", 5),
                Column("Name", 18),
                Column("Unicode", 9),
                Column("Coined", 8),
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
        title = Style().bold().foreground(get_theme().primary).render("Punctuation marks")
        row = self.table.selected_row()
        selected = Style().faint().render(f"selected: {row[1] if row else '-'}")
        hint = Style().faint().render("↑/↓ move · q quit")
        return f"\n{title}\n\n{self.table.view()}\n\n{selected}\n{hint}\n"


if __name__ == "__main__":
    from _shared import run_example

    run_example(Model())
