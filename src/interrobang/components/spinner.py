"""An animated spinner for indicating background activity.

Drive it by returning :meth:`Spinner.tick` from your ``init`` (and again each
time you receive a :class:`SpinnerTickMsg`); the spinner re-issues its own tick
so the animation keeps running::

    class Model:
        def __init__(self):
            self.spinner = Spinner(DOTS)

        def init(self):
            return self.spinner.tick

        def update(self, msg):
            self.spinner, cmd = self.spinner.update(msg)
            return self, cmd

        def view(self):
            return self.spinner.view() + " loading..."
"""

from __future__ import annotations

import itertools
import time
from dataclasses import dataclass

from ..command import Cmd
from ..style import Style

__all__ = [
    "SpinnerStyle",
    "SpinnerTickMsg",
    "Spinner",
    "LINE",
    "DOTS",
    "MINI_DOT",
    "JUMP",
    "PULSE",
    "POINTS",
    "GLOBE",
    "MOON",
    "MONKEY",
    "METER",
    "HAMBURGER",
    "ELLIPSIS",
]


@dataclass(frozen=True)
class SpinnerStyle:
    """A spinner animation: its frames and how fast to cycle them."""

    frames: tuple[str, ...]
    fps: float  # frames per second


LINE = SpinnerStyle(("|", "/", "-", "\\"), 10)
DOTS = SpinnerStyle(("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"), 12)
MINI_DOT = SpinnerStyle(("⠷", "⠯", "⠟", "⠻", "⠽", "⠾"), 12)
JUMP = SpinnerStyle(("⢄", "⢂", "⢁", "⡁", "⡈", "⡐", "⡠"), 10)
PULSE = SpinnerStyle(("█", "▓", "▒", "░"), 8)
POINTS = SpinnerStyle(("∙∙∙", "●∙∙", "∙●∙", "∙∙●"), 7)
GLOBE = SpinnerStyle(("🌍", "🌎", "🌏"), 4)
MOON = SpinnerStyle(("🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"), 8)
MONKEY = SpinnerStyle(("🙈", "🙉", "🙊"), 3)
METER = SpinnerStyle(("▱▱▱", "▰▱▱", "▰▰▱", "▰▰▰", "▰▰▱", "▰▱▱"), 7)
HAMBURGER = SpinnerStyle(("☱", "☲", "☴", "☲"), 5)
ELLIPSIS = SpinnerStyle(("   ", ".  ", ".. ", "..."), 4)


@dataclass(frozen=True)
class SpinnerTickMsg:
    """Sent to advance a spinner. Carries the spinner's id so multiple spinners
    on screen do not interfere with one another."""

    id: int


class Spinner:
    """A spinning activity indicator."""

    _ids = itertools.count()

    def __init__(self, spinner: SpinnerStyle = DOTS, style: Style | None = None):
        self.spinner = spinner
        self.style = style if style is not None else Style()
        self.frame = 0
        self.id = next(Spinner._ids)

    @property
    def tick(self) -> Cmd:
        """A command that waits one frame then emits this spinner's tick message."""
        spinner = self.spinner
        spinner_id = self.id

        def cmd() -> SpinnerTickMsg:
            time.sleep(1.0 / spinner.fps)
            return SpinnerTickMsg(spinner_id)

        return cmd

    def update(self, msg: object) -> "tuple[Spinner, Cmd | None]":
        """Advance the frame on our own tick; ignore everything else."""
        if isinstance(msg, SpinnerTickMsg) and msg.id == self.id:
            self.frame = (self.frame + 1) % len(self.spinner.frames)
            return self, self.tick
        return self, None

    def view(self) -> str:
        """Render the current frame."""
        return self.style.render(self.spinner.frames[self.frame])
