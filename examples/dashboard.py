"""A small dashboard composing several components. Run: python examples/dashboard.py.

Shows a spinner, an animated progress bar, and a navigable list side by side --
the kind of layout you build by giving each component its own ``update``/``view``
and arranging the results with the layout helpers. Colors come from the active
theme (Solarized Dark by default); try ``irb.set_theme(irb.NEON)`` in ``main``.
"""

from dataclasses import dataclass

import interrobang as irb
from interrobang import (
    SOLARIZED_DARK,
    SOLARIZED_LIGHT,
    KeyMsg,
    batch,
    disable_background_fill,
    enable_background_fill,
    get_theme,
    quit,
    set_theme,
    tick,
)
from interrobang.components import DOTS, Item, List, Progress, Spinner
from interrobang.style import ROUNDED, TOP, Style, join_horizontal, join_vertical


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
        self.theme = get_theme()
        self.fill = False
        self.spinner = Spinner(DOTS)  # themed accent by default
        self.progress = Progress(width=30)  # themed gradient by default
        self.list = List(TASKS, width=30, height=10)
        self.list.title = "Pipeline"
        self.list.show_description = False
        self.list.show_status_bar = False

    def init(self):
        return batch(self.spinner.tick, tick(0.1, FrameMsg))

    def update(self, msg):
        cmds = []
        if isinstance(msg, KeyMsg):
            if msg.key in ("q", "ctrl+c", "esc"):
                return self, quit
            if msg.key == "t":  # toggle theme (re-styles everything live)
                set_theme(SOLARIZED_LIGHT if self.theme is SOLARIZED_DARK else SOLARIZED_DARK)
                self.theme = get_theme()
            elif msg.key == "f":  # toggle full-screen background fill
                self.fill = not self.fill
                cmds.append(enable_background_fill if self.fill else disable_background_fill)
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
        t = self.theme
        header = (
            Style().bold().foreground(t.on_primary).background(t.primary).padding(0, 2)
            .render("interrobang dashboard ‽")
        )
        status_panel = Style().border(ROUNDED).border_foreground(t.secondary).padding(1, 2).width(36)
        status_body = join_vertical(
            0.0,
            f"{self.spinner.view()} working...",
            "",
            "Build progress:",
            self.progress.view(),
        )
        list_panel = Style().border(ROUNDED).border_foreground(t.faint).padding(1, 2)
        panels = join_horizontal(
            TOP,
            status_panel.render(status_body),
            "  ",
            list_panel.render(self.list.view()),
        )
        footer = Style().foreground(t.muted).render("↑/↓ move · t theme · f fill · q quit")
        return f"\n{header}\n\n{panels}\n\n{footer}"


if __name__ == "__main__":
    from _shared import run_example

    run_example(Dashboard())
