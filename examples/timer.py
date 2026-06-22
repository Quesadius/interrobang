"""A one-second-tick countdown timer. Run: python examples/timer.py."""

from dataclasses import dataclass

import interrobang as irb
from interrobang import KeyMsg, quit, every
from interrobang.style import Color, Style


@dataclass(frozen=True)
class TickMsg:
    t: float


class Model:
    def __init__(self, seconds=10):
        self.remaining = seconds
        self.running = True

    def init(self):
        return every(1.0, TickMsg)

    def update(self, msg):
        if isinstance(msg, KeyMsg):
            if msg.key in ("q", "ctrl+c", "esc"):
                return self, quit
            if msg.key == " " or msg.key == "space":
                self.running = not self.running
        if isinstance(msg, TickMsg) and self.running:
            self.remaining -= 1
            if self.remaining <= 0:
                self.remaining = 0
                return self, quit
            return self, every(1.0, TickMsg)
        if isinstance(msg, TickMsg):
            return self, every(1.0, TickMsg)
        return self, None

    def view(self):
        big = Style().bold().foreground(Color("#FAFAFA")).background(Color("#7D56F4")).padding(1, 3)
        state = "running" if self.running else "paused"
        return (
            f"\n{big.render(f'{self.remaining:02d}s')}\n\n"
            f"  {Style().faint().render(f'{state} · space pause/resume · q quit')}\n"
        )


if __name__ == "__main__":
    from _shared import apply_theme_flag

    apply_theme_flag()
    irb.run(Model(), alt_screen=True)
