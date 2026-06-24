"""A selectable, filterable list. Run: python examples/list.py.

Move with ↑/↓ (or j/k), filter with /, select with enter, q to quit.
"""

import interrobang as irb
from interrobang import KeyMsg, quit
from interrobang.components import Item, List
from interrobang.style import Style

MARKS = [
    Item("Interrobang", "‽  asks and exclaims at once"),
    Item("Exclamation point", "!  emphatic and eager"),
    Item("Question mark", "?  curious and uncertain"),
    Item("Em dash", "—  an abrupt aside"),
    Item("Ellipsis", "…  a trailing off"),
    Item("Semicolon", ";  joins two related clauses"),
    Item("Ampersand", "&  the ligature of “et”"),
    Item("Octothorpe", "#  hash, pound, sharp"),
    Item("Pilcrow", "¶  marks a new paragraph"),
    Item("Asterisk", "*  a footnote’s little star"),
]


class Model:
    def __init__(self):
        self.list = List(MARKS, width=44, height=16)
        self.list.title = "Punctuation"
        self.chosen = None

    def init(self):
        return None

    def update(self, msg):
        if isinstance(msg, KeyMsg):
            if msg.key in ("ctrl+c", "q") and not self.list.filtering:
                return self, quit
            if msg.key == "enter" and not self.list.filtering:
                item = self.list.selected_item()
                if item:
                    self.chosen = item.title
                    return self, quit
        self.list, cmd = self.list.update(msg)
        return self, cmd

    def view(self):
        hint = Style().faint().render("↑/↓ move · / filter · enter select · q quit")
        return self.list.view() + "\n\n" + hint


if __name__ == "__main__":
    from _shared import run_example

    final = run_example(Model())
    if final.chosen:
        print(f"You chose: {final.chosen}")
