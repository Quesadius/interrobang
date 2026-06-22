"""An animated gradient progress bar. Run: python examples/progress.py."""

from dataclasses import dataclass

import interrobang as irb
from interrobang import KeyMsg, quit, tick
from interrobang.components import Progress
from interrobang.style import Style


@dataclass(frozen=True)
class FrameMsg:
    t: float


class Model:
    def __init__(self):
        self.bar = Progress(width=50)  # gradient comes from the active theme
        self.done = False

    def init(self):
        return tick(0.08, FrameMsg)

    def update(self, msg):
        if isinstance(msg, KeyMsg) and msg.key in ("q", "ctrl+c", "esc"):
            return self, quit
        if isinstance(msg, FrameMsg) and not self.done:
            self.bar.incr_percent(0.015)
            if self.bar.percent >= 1.0:
                self.done = True
                return self, None
            return self, tick(0.08, FrameMsg)
        return self, None

    def view(self):
        status = "Done! ✓" if self.done else "Downloading..."
        return (
            f"\n  {Style().bold().render(status)}\n\n"
            f"  {self.bar.view()}\n\n"
            f"  {Style().faint().render('q quit')}\n"
        )


if __name__ == "__main__":
    from _shared import run_example

    run_example(Model())
