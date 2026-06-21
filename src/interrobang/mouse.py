"""Mouse input: :class:`MouseMsg` and its button/action enums.

Mouse reporting is off by default. Turn it on by running your program with
``mouse=True`` (or by sending :func:`interrobang.enable_mouse`). Coordinates are
zero-based cell offsets from the top-left of the screen.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

__all__ = ["MouseButton", "MouseAction", "MouseMsg"]


class MouseButton(Enum):
    """Which mouse button (or wheel direction) an event refers to."""

    NONE = auto()
    LEFT = auto()
    MIDDLE = auto()
    RIGHT = auto()
    WHEEL_UP = auto()
    WHEEL_DOWN = auto()
    WHEEL_LEFT = auto()
    WHEEL_RIGHT = auto()


class MouseAction(Enum):
    """What happened: a press, a release, or motion."""

    PRESS = auto()
    RELEASE = auto()
    MOTION = auto()


@dataclass(frozen=True)
class MouseMsg:
    """A mouse event at cell ``(x, y)`` (both zero-based)."""

    x: int
    y: int
    button: MouseButton = MouseButton.NONE
    action: MouseAction = MouseAction.PRESS
    alt: bool = False
    ctrl: bool = False
    shift: bool = False

    @property
    def is_wheel(self) -> bool:
        """True if this event is a scroll-wheel movement."""
        return self.button in (
            MouseButton.WHEEL_UP,
            MouseButton.WHEEL_DOWN,
            MouseButton.WHEEL_LEFT,
            MouseButton.WHEEL_RIGHT,
        )
