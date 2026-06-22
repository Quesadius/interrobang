"""A scrollable viewport over long text. Run: python examples/viewport.py.

Scroll with arrows / j / k / PgUp / PgDn / g / G; q to quit.
"""

import interrobang as irb
from interrobang import KeyMsg, WindowSizeMsg, quit
from interrobang.components import Viewport
from interrobang.style import ROUNDED, Color, Style

PARAGRAPHS = [
    f"{i:>3}. The interrobang (‽) combines a question mark and an exclamation "
    "point. It is the perfect mascot for a toolkit about interactive, expressive "
    "terminal interfaces."
    for i in range(1, 61)
]
TEXT = "\n".join(PARAGRAPHS)


class Model:
    def __init__(self):
        self.vp = Viewport(width=70, height=18)
        self.vp.set_content(TEXT)

    def init(self):
        return None

    def update(self, msg):
        if isinstance(msg, KeyMsg) and msg.key in ("q", "ctrl+c", "esc"):
            return self, quit
        if isinstance(msg, WindowSizeMsg):
            self.vp.width = min(70, msg.width - 4)
            self.vp.height = max(3, msg.height - 4)
            self.vp.set_content(TEXT)
        self.vp, cmd = self.vp.update(msg)
        return self, cmd

    def view(self):
        frame = Style().border(ROUNDED).border_foreground(Color("#7D56F4"))
        pct = int(self.vp.scroll_percent() * 100)
        footer = Style().faint().render(f"{pct}% · ↑/↓ scroll · q quit")
        return frame.render(self.vp.view()) + "\n" + footer


if __name__ == "__main__":
    from _shared import run_example

    run_example(Model())
