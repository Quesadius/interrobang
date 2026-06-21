"""A small dashboard composing several components. Run: python examples/dashboard.py.

Shows a spinner, an animated progress bar, and a navigable list side by side --
the kind of layout you build by giving each component its own ``update``/``view``
and arranging the results with the layout helpers.
"""

from dataclasses import dataclass

import interrobang as irb
from interrobang import KeyMsg, WindowSizeMsg, batch, quit, tick
from interrobang.components import DOTS, Item, List, Progress, Spinner
from interrobang.style import ROUNDED, TOP, Color, Style, join_horizontal, join_vertical


@dataclass(frozen=True)
class FrameMsg:
    t: float


TASKS = [
    Item("Fetch dependencies"),
    Item("Compile sources"),
    Item("Run tests"),
    Item("Build artifacts"),
    Item("Package release"),
    Item("Publish"),
]


class Dashboard:
    def __init__(self):
        self.spinner = Spinner(DOTS, Style().foreground(Color("#FF7CCB")))
        self.progress = Progress(width=30).with_gradient("#FF7CCB", "#FDFF8C")
        self.list = List(TASKS, width=30, height=10)
        self.list.title = "Pipeline"
        self.list.show_description = False
        self.list.show_status_bar = False

    def init(self):
        return batch(self.spinner.tick, tick(0.1, FrameMsg))

    def update(self, msg):
        cmds = []
        if isinstance(msg, KeyMsg) and msg.key in ("q", "ctrl+c", "esc"):
            return self, quit
        if isinstance(msg, FrameMsg):
            self.progress.incr_percent(0.012)
            if self.progress.percent >= 1.0:
                self.progress.set_percent(0.0)
            cmds.append(tick(0.1, FrameMsg))

        self.spinner, spin_cmd = self.spinner.update(msg)
        cmds.append(spin_cmd)
        self.list, _ = self.list.update(msg)
        return self, batch(*cmds)

    def view(self):
        header = (
            Style()
            .bold()
            .foreground(Color("#FAFAFA"))
            .background(Color("#7D56F4"))
            .padding(0, 2)
            .render("interrobang dashboard ‽")
        )

        status_panel = Style().border(ROUNDED).border_foreground(Color("63")).padding(1, 2).width(36)
        status_body = join_vertical(
            0.0,
            f"{self.spinner.view()} working...",
            "",
            "Build progress:",
            self.progress.view(),
        )

        list_panel = Style().border(ROUNDED).border_foreground(Color("240")).padding(1, 2)

        panels = join_horizontal(
            TOP,
            status_panel.render(status_body),
            "  ",
            list_panel.render(self.list.view()),
        )

        footer = Style().faint().render("↑/↓ move the list · q quit")
        return f"\n{header}\n\n{panels}\n\n{footer}\n"


if __name__ == "__main__":
    irb.run(Dashboard(), alt_screen=True)
