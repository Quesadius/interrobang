"""interrobang -- build beautiful terminal UIs in Python. ‽

interrobang gives you two things, mirroring Charm's Bubble Tea and Lip Gloss:

* a tiny **runtime** built on the Elm Architecture (model / update / view), and
* a **styling engine** for color, layout, and borders.

The thirty-second tour::

    import interrobang as irb
    from interrobang import KeyMsg, quit
    from interrobang.style import Style, Color

    class Counter:
        def __init__(self):
            self.n = 0

        def init(self):
            return None

        def update(self, msg):
            if isinstance(msg, KeyMsg):
                if msg.key in ("q", "ctrl+c"):
                    return self, quit
                if msg.key == "up":
                    self.n += 1
                if msg.key == "down":
                    self.n -= 1
            return self, None

        def view(self):
            return Style().bold().foreground(Color("#7D56F4")).render(f"Count: {self.n}")

    if __name__ == "__main__":
        irb.run(Counter(), alt_screen=True)

See :mod:`interrobang.style` for styling, :mod:`interrobang.components` for
ready-made widgets, and :mod:`interrobang.testing` for testing helpers.
"""

from __future__ import annotations

from ._ansi import string_width, strip_ansi, truncate, wrap
from .command import (
    Cmd,
    Command,
    batch,
    clear_screen,
    disable_background_fill,
    disable_mouse,
    enable_background_fill,
    enable_mouse,
    enter_alt_screen,
    every,
    exit_alt_screen,
    hide_cursor,
    quit,
    sequence,
    set_window_title,
    show_cursor,
    tick,
)
from .key import KeyMsg, KeyType
from .message import (
    Msg,
    QuitMsg,
    ResumeMsg,
    SuspendMsg,
    WindowSizeMsg,
)
from .model import Model
from .mouse import MouseAction, MouseButton, MouseMsg
from .program import Program, detect_dark_background, detect_profile, run
from .style import Color, Style
from .theme import CHARM, SOLARIZED_DARK, SOLARIZED_LIGHT, Theme, get_theme, set_theme

__version__ = "0.1.0"

__all__ = [
    "__version__",
    # runtime
    "Program",
    "run",
    "Model",
    "detect_profile",
    "detect_dark_background",
    # messages
    "Msg",
    "KeyMsg",
    "KeyType",
    "MouseMsg",
    "MouseButton",
    "MouseAction",
    "WindowSizeMsg",
    "QuitMsg",
    "SuspendMsg",
    "ResumeMsg",
    # commands
    "Cmd",
    "Command",
    "quit",
    "batch",
    "sequence",
    "tick",
    "every",
    "enter_alt_screen",
    "exit_alt_screen",
    "hide_cursor",
    "show_cursor",
    "enable_mouse",
    "disable_mouse",
    "enable_background_fill",
    "disable_background_fill",
    "clear_screen",
    "set_window_title",
    # styling (most-used; full set in interrobang.style)
    "Style",
    "Color",
    # theming
    "Theme",
    "SOLARIZED_DARK",
    "SOLARIZED_LIGHT",
    "CHARM",
    "set_theme",
    "get_theme",
    # text utilities
    "string_width",
    "strip_ansi",
    "truncate",
    "wrap",
]
