"""An animated spinner. Run: python examples/spinner.py (q to quit)."""

import interrobang as irb
from interrobang import KeyMsg, quit
from interrobang.components import DOTS, Spinner
from interrobang.style import Color, Style


class Model:
    def __init__(self):
        self.spinner = Spinner(DOTS, Style().foreground(Color("#FF7CCB")))

    def init(self):
        return self.spinner.tick

    def update(self, msg):
        if isinstance(msg, KeyMsg) and msg.key in ("q", "ctrl+c", "esc"):
            return self, quit
        self.spinner, cmd = self.spinner.update(msg)
        return self, cmd

    def view(self):
        return (
            f"\n  {self.spinner.view()} Brewing your interface...\n\n"
            f"  {Style().faint().render('q quit')}\n"
        )


if __name__ == "__main__":
    irb.run(Model(), alt_screen=True)
