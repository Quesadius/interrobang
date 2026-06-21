"""Messages -- the events that flow into your ``update`` method.

In the Elm Architecture, *everything* that happens is a message: a key press, a
window resize, a timer firing, a background task finishing. A message can be any
Python object; you decide what your own messages look like. This module defines
the handful the runtime produces itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .key import KeyMsg, KeyType
from .mouse import MouseAction, MouseButton, MouseMsg

__all__ = [
    "Msg",
    "KeyMsg",
    "KeyType",
    "MouseMsg",
    "MouseButton",
    "MouseAction",
    "WindowSizeMsg",
    "QuitMsg",
    "ResumeMsg",
    "SuspendMsg",
]

#: A message is any object. The built-in ones are defined here; yours can be
#: anything (a dataclass, a tuple, a string -- whatever you like).
Msg = Any


@dataclass(frozen=True)
class WindowSizeMsg:
    """Sent on startup and whenever the terminal is resized."""

    width: int
    height: int


@dataclass(frozen=True)
class QuitMsg:
    """Tells the runtime to shut down. Usually produced by the ``quit`` command."""


@dataclass(frozen=True)
class SuspendMsg:
    """Sent just before the program suspends to the background (Ctrl+Z)."""


@dataclass(frozen=True)
class ResumeMsg:
    """Sent when the program resumes from the background."""
