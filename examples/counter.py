"""The smallest complete interrobang app: a counter.

Run it::

    python examples/counter.py

Press up/down (or k/j, or +/-) to change the count, q to quit.
"""

import interrobang as irb
from interrobang import KeyMsg, quit
from interrobang.style import Color, Style


class Counter:
    def __init__(self):
        self.count = 0

    def init(self):
        return None

    def update(self, msg):
        if isinstance(msg, KeyMsg):
            if msg.key in ("q", "ctrl+c", "esc"):
                return self, quit
            if msg.key in ("up", "k", "+"):
                self.count += 1
            elif msg.key in ("down", "j", "-"):
                self.count -= 1
        return self, None

    def view(self):
        title = Style().bold().foreground(Color("#7D56F4"))
        number = Style().bold().foreground(Color("#FAFAFA")).background(Color("#7D56F4")).padding(0, 2)
        hint = Style().faint()
        return "\n".join(
            [
                title.render("interrobang counter"),
                "",
                "  " + number.render(str(self.count)),
                "",
                hint.render("  ↑/↓ change · q quit"),
            ]
        )


if __name__ == "__main__":
    irb.run(Counter(), alt_screen=True)
