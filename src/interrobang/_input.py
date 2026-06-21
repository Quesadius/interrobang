"""Parse raw terminal input bytes into key and mouse messages.

Terminals report input as a byte stream peppered with escape sequences. This
module turns that stream into :class:`~interrobang.key.KeyMsg` and
:class:`~interrobang.mouse.MouseMsg` objects. It is deliberately pure -- bytes
in, events out -- so it can be tested exhaustively without a real terminal.

The main entry point is :func:`parse`, which consumes as many complete events as
it can and hands back any trailing partial sequence so the caller can prepend
more bytes and try again.
"""

from __future__ import annotations

from dataclasses import replace

from .key import KeyMsg, KeyType
from .mouse import MouseAction, MouseButton, MouseMsg

# CSI final byte -> key (arrows, navigation, and the F1-F4 "CSI" form).
_CSI_FINAL: dict[str, KeyType] = {
    "A": KeyType.UP,
    "B": KeyType.DOWN,
    "C": KeyType.RIGHT,
    "D": KeyType.LEFT,
    "H": KeyType.HOME,
    "F": KeyType.END,
    "P": KeyType.F1,
    "Q": KeyType.F2,
    "R": KeyType.F3,
    "S": KeyType.F4,
}

# CSI "<n>~" sequences.
_TILDE: dict[int, KeyType] = {
    1: KeyType.HOME,
    2: KeyType.INSERT,
    3: KeyType.DELETE,
    4: KeyType.END,
    5: KeyType.PGUP,
    6: KeyType.PGDOWN,
    7: KeyType.HOME,
    8: KeyType.END,
    11: KeyType.F1,
    12: KeyType.F2,
    13: KeyType.F3,
    14: KeyType.F4,
    15: KeyType.F5,
    17: KeyType.F6,
    18: KeyType.F7,
    19: KeyType.F8,
    20: KeyType.F9,
    21: KeyType.F10,
    23: KeyType.F11,
    24: KeyType.F12,
}

# SS3 sequences (ESC O <byte>): F1-F4 plus application-mode arrows.
_SS3: dict[str, KeyType] = {
    "P": KeyType.F1,
    "Q": KeyType.F2,
    "R": KeyType.F3,
    "S": KeyType.F4,
    "A": KeyType.UP,
    "B": KeyType.DOWN,
    "C": KeyType.RIGHT,
    "D": KeyType.LEFT,
    "H": KeyType.HOME,
    "F": KeyType.END,
}


def _modifiers(mod: int) -> tuple[bool, bool, bool]:
    """Decode an xterm modifier parameter into ``(alt, ctrl, shift)``."""
    bits = max(0, mod - 1)
    return bool(bits & 2), bool(bits & 4), bool(bits & 1)


def _utf8_len(lead: int) -> int:
    """Return the byte length of a UTF-8 sequence from its lead byte (0 if bad)."""
    if lead & 0x80 == 0:
        return 1
    if lead & 0xE0 == 0xC0:
        return 2
    if lead & 0xF0 == 0xE0:
        return 3
    if lead & 0xF8 == 0xF0:
        return 4
    return 0


def _single_byte(b: int) -> list[KeyMsg]:
    """Map a single non-escape byte to a key event."""
    if b in (0x0D, 0x0A):
        return [KeyMsg(KeyType.ENTER)]
    if b == 0x09:
        return [KeyMsg(KeyType.TAB)]
    if b == 0x7F:
        return [KeyMsg(KeyType.BACKSPACE)]
    if b == 0x00:
        return [KeyMsg(KeyType.RUNES, "@", ctrl=True)]
    if 1 <= b <= 26:
        return [KeyMsg(KeyType.RUNES, chr(b + 96), ctrl=True)]
    if b == 0x1B:
        return [KeyMsg(KeyType.ESC)]
    if b == 0x20:
        return [KeyMsg(KeyType.SPACE, " ")]
    if 0x1C <= b <= 0x1F:
        return [KeyMsg(KeyType.RUNES, {0x1C: "\\", 0x1D: "]", 0x1E: "^", 0x1F: "_"}[b], ctrl=True)]
    if 0x21 <= b <= 0x7E:
        return [KeyMsg(KeyType.RUNES, chr(b))]
    return []


def _parse_mouse(params: list[int], final: str) -> list[MouseMsg]:
    if len(params) < 3:
        return []
    b, x, y = params[0], params[1], params[2]
    shift = bool(b & 4)
    alt = bool(b & 8)
    ctrl = bool(b & 16)
    motion = bool(b & 32)
    wheel = bool(b & 64)
    low = b & 3
    if wheel:
        button = {
            0: MouseButton.WHEEL_UP,
            1: MouseButton.WHEEL_DOWN,
            2: MouseButton.WHEEL_LEFT,
            3: MouseButton.WHEEL_RIGHT,
        }[low]
        action = MouseAction.PRESS
    else:
        button = {
            0: MouseButton.LEFT,
            1: MouseButton.MIDDLE,
            2: MouseButton.RIGHT,
            3: MouseButton.NONE,
        }[low]
        if motion:
            action = MouseAction.MOTION
        elif final == "m":
            action = MouseAction.RELEASE
        else:
            action = MouseAction.PRESS
    return [MouseMsg(x - 1, y - 1, button, action, alt=alt, ctrl=ctrl, shift=shift)]


def _map_csi(params: list[int], final: str) -> list:
    main = params[0] if params else 1
    mod = params[1] if len(params) >= 2 else 1
    alt, ctrl, shift = _modifiers(mod)
    if final == "~":
        kt = _TILDE.get(main)
        return [KeyMsg(kt, alt=alt, ctrl=ctrl, shift=shift)] if kt else []
    if final == "Z":
        return [KeyMsg(KeyType.TAB, shift=True)]
    kt = _CSI_FINAL.get(final)
    return [KeyMsg(kt, alt=alt, ctrl=ctrl, shift=shift)] if kt else []


def _parse_csi(buf: bytes, i: int, flush: bool) -> tuple[int, list]:
    n = len(buf)
    j = i + 2
    mouse = False
    if j < n and buf[j] == ord("<"):
        mouse = True
        j += 1
    elif j < n and buf[j] == ord("?"):
        j += 1
    start = j
    while j < n and (chr(buf[j]).isdigit() or buf[j] == ord(";")):
        j += 1
    if j >= n:
        return (1, [KeyMsg(KeyType.ESC)]) if flush else (0, [])
    final = chr(buf[j])
    consumed = (j - i) + 1
    param_str = buf[start:j].decode("ascii", "ignore")
    params = [int(p) for p in param_str.split(";") if p != ""]
    if mouse:
        return consumed, _parse_mouse(params, final)
    return consumed, _map_csi(params, final)


def _parse_escape(buf: bytes, i: int, flush: bool) -> tuple[int, list]:
    n = len(buf)
    if i + 1 >= n:
        return (1, [KeyMsg(KeyType.ESC)]) if flush else (0, [])
    c1 = buf[i + 1]
    if c1 == ord("["):
        return _parse_csi(buf, i, flush)
    if c1 == ord("O"):
        if i + 2 >= n:
            return (1, [KeyMsg(KeyType.ESC)]) if flush else (0, [])
        kt = _SS3.get(chr(buf[i + 2]))
        if kt:
            return 3, [KeyMsg(kt)]
        return 1, [KeyMsg(KeyType.ESC)]
    if c1 == 0x1B:
        return 1, [KeyMsg(KeyType.ESC)]
    # Alt + key: the next byte is an ordinary key with Alt held.
    out = [replace(m, alt=True) for m in _single_byte(c1)]
    return 2, out


def parse(buffer: bytes, flush: bool = False) -> tuple[list, bytes]:
    """Parse *buffer*, returning ``(events, remaining_bytes)``.

    Complete events are returned in order. A trailing incomplete escape or
    multi-byte sequence is left in ``remaining_bytes`` so the caller can append
    more input and call again. Pass ``flush=True`` to force a dangling ``ESC``
    to be emitted as a standalone Escape key (used after an input timeout).
    """
    events: list = []
    i = 0
    n = len(buffer)
    while i < n:
        b = buffer[i]
        if b == 0x1B:
            consumed, msgs = _parse_escape(buffer, i, flush)
            if consumed == 0:
                break
            events.extend(msgs)
            i += consumed
            continue
        if b < 0x80:
            events.extend(_single_byte(b))
            i += 1
            continue
        length = _utf8_len(b)
        if length == 0:
            i += 1
            continue
        if i + length > n:
            break
        try:
            events.append(KeyMsg(KeyType.RUNES, runes=buffer[i : i + length].decode("utf-8")))
            i += length
        except UnicodeDecodeError:
            i += 1
    return events, buffer[i:]
