"""A filesystem browser. Run: python examples/filepicker.py.

↑/↓ move · enter/→ open · backspace/← up · . toggle hidden · q quit.
"""

import interrobang as irb
from interrobang import KeyMsg, quit
from interrobang.components import FilePicker
from interrobang.style import Color, Style


class Model:
    def __init__(self):
        self.picker = FilePicker(path=".", height=18)
        self.chosen = None

    def init(self):
        return None

    def update(self, msg):
        if isinstance(msg, KeyMsg) and msg.key in ("q", "ctrl+c", "esc"):
            return self, quit
        self.picker, cmd = self.picker.update(msg)
        chosen = self.picker.did_select_file()
        if chosen:
            self.chosen = chosen
            return self, quit
        return self, cmd

    def view(self):
        title = Style().bold().foreground(Color("#7D56F4")).render("Pick a file")
        hint = Style().faint().render("↑/↓ move · enter open · backspace up · q quit")
        return f"\n  {title}\n\n{self.picker.view()}\n\n  {hint}\n"


if __name__ == "__main__":
    from _shared import run_example

    final = run_example(Model())
    if final.chosen:
        print(f"You picked: {final.chosen}")
