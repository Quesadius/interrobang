"""Keyboard input: key types and the :class:`KeyMsg` your ``update`` receives.

When the user presses a key, the runtime delivers a :class:`KeyMsg`. The most
ergonomic way to react is to compare its canonical name::

    def update(self, msg):
        if isinstance(msg, KeyMsg):
            if msg.key == "ctrl+c":
                return self, quit
            if msg.key == "enter":
                ...
            if msg.type is KeyType.RUNES:
                self.text += msg.runes

Canonical names look like ``"a"``, ``"A"``, ``"enter"``, ``"ctrl+c"``,
``"alt+left"``, ``"shift+tab"`` -- modifiers first, in ``ctrl+alt+shift`` order.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

__all__ = ["KeyType", "KeyMsg"]


class KeyType(Enum):
    """The kind of key in a :class:`KeyMsg`.

    Printable characters all share :data:`RUNES` (the character is in
    ``KeyMsg.runes``); every other member names a specific non-printable key.
    """

    RUNES = auto()
    ENTER = auto()
    TAB = auto()
    SPACE = auto()
    BACKSPACE = auto()
    DELETE = auto()
    INSERT = auto()
    ESC = auto()
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    HOME = auto()
    END = auto()
    PGUP = auto()
    PGDOWN = auto()
    F1 = auto()
    F2 = auto()
    F3 = auto()
    F4 = auto()
    F5 = auto()
    F6 = auto()
    F7 = auto()
    F8 = auto()
    F9 = auto()
    F10 = auto()
    F11 = auto()
    F12 = auto()


_KEY_NAMES: dict[KeyType, str] = {
    KeyType.ENTER: "enter",
    KeyType.TAB: "tab",
    KeyType.SPACE: "space",
    KeyType.BACKSPACE: "backspace",
    KeyType.DELETE: "delete",
    KeyType.INSERT: "insert",
    KeyType.ESC: "esc",
    KeyType.UP: "up",
    KeyType.DOWN: "down",
    KeyType.LEFT: "left",
    KeyType.RIGHT: "right",
    KeyType.HOME: "home",
    KeyType.END: "end",
    KeyType.PGUP: "pgup",
    KeyType.PGDOWN: "pgdown",
    KeyType.F1: "f1",
    KeyType.F2: "f2",
    KeyType.F3: "f3",
    KeyType.F4: "f4",
    KeyType.F5: "f5",
    KeyType.F6: "f6",
    KeyType.F7: "f7",
    KeyType.F8: "f8",
    KeyType.F9: "f9",
    KeyType.F10: "f10",
    KeyType.F11: "f11",
    KeyType.F12: "f12",
}


@dataclass(frozen=True)
class KeyMsg:
    """A single key press.

    Attributes:
        type: The :class:`KeyType`. For ordinary characters this is
            :data:`KeyType.RUNES` and the character is in ``runes``.
        runes: The character(s) typed (only meaningful for ``RUNES``).
        alt: Whether Alt/Meta was held.
        ctrl: Whether Ctrl was held (set for control-character keys).
        shift: Whether Shift was held (only set for non-printable keys; for
            printable keys, Shift is already reflected in the character itself).
    """

    type: KeyType
    runes: str = ""
    alt: bool = False
    ctrl: bool = False
    shift: bool = False

    def __str__(self) -> str:
        parts: list[str] = []
        if self.ctrl:
            parts.append("ctrl")
        if self.alt:
            parts.append("alt")
        if self.shift:
            parts.append("shift")
        base = self.runes if self.type is KeyType.RUNES else _KEY_NAMES[self.type]
        parts.append(base)
        return "+".join(parts)

    @property
    def key(self) -> str:
        """The canonical name of this key, e.g. ``"ctrl+c"`` or ``"enter"``."""
        return str(self)
