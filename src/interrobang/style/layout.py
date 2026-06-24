"""Layout primitives: alignment, padding, joining, and placement.

These functions operate on plain (possibly already-styled) strings and are
ANSI-aware: they measure visible width while leaving escape sequences intact.
They are the composition glue you use to arrange rendered blocks next to and on
top of one another (``join_horizontal``, ``join_vertical``, ``place``).

Positions are floats in ``[0, 1]``: ``0.0`` is left/top, ``0.5`` is center,
``1.0`` is right/bottom. The named constants below cover the common cases.
"""

from __future__ import annotations

from .._ansi import max_line_width, string_width

__all__ = [
    "LEFT",
    "CENTER",
    "RIGHT",
    "TOP",
    "BOTTOM",
    "pad_right",
    "align_horizontal",
    "align_vertical",
    "join_horizontal",
    "join_vertical",
    "place",
    "place_horizontal",
    "place_vertical",
]

LEFT: float = 0.0
CENTER: float = 0.5
RIGHT: float = 1.0
TOP: float = 0.0
BOTTOM: float = 1.0


def _split_gap(gap: int, position: float) -> tuple[int, int]:
    """Split *gap* cells into (leading, trailing) for the given position."""
    if gap <= 0:
        return 0, 0
    leading = int(round(gap * _clamp(position)))
    return leading, gap - leading


def _clamp(position: float) -> float:
    return 0.0 if position < 0 else 1.0 if position > 1 else position


def pad_right(line: str, width: int, fill: str = " ") -> str:
    """Pad a single *line* with *fill* on the right to reach *width* cells."""
    gap = width - string_width(line)
    return line + fill * gap if gap > 0 else line


def align_horizontal(text: str, width: int, position: float = LEFT, fill: str = " ") -> str:
    """Pad every line of *text* to *width* cells, positioning content per *position*.

    Lines already wider than *width* are left untouched. This makes a ragged
    block of text rectangular, which is what most layout operations need.
    """
    out: list[str] = []
    for line in text.split("\n"):
        gap = width - string_width(line)
        left, right = _split_gap(gap, position)
        out.append(fill * left + line + fill * right)
    return "\n".join(out)


def align_vertical(text: str, height: int, position: float = TOP) -> str:
    """Pad *text* to *height* lines, positioning content per *position*.

    New lines are empty strings; combine with :func:`align_horizontal` if you
    need a solid rectangle. Content taller than *height* is returned unchanged.
    """
    lines = text.split("\n")
    gap = height - len(lines)
    if gap <= 0:
        return text
    top, bottom = _split_gap(gap, position)
    return "\n".join([""] * top + lines + [""] * bottom)


def join_horizontal(position: float, *blocks: str) -> str:
    """Join *blocks* side by side, aligning them vertically per *position*.

    Each block may be multi-line; shorter blocks are padded with blank lines so
    every block contributes the same number of rows.
    """
    blocks = tuple(b for b in blocks if b is not None)
    if not blocks:
        return ""
    split = [b.split("\n") for b in blocks]
    height = max(len(lines) for lines in split)
    widths = [max_line_width(b) for b in blocks]

    # Vertically pad each block to the common height.
    for lines in split:
        gap = height - len(lines)
        if gap:
            top, bottom = _split_gap(gap, position)
            lines[:0] = [""] * top
            lines.extend([""] * bottom)

    rows: list[str] = []
    for row in range(height):
        cells = []
        for block_index, lines in enumerate(split):
            cells.append(pad_right(lines[row], widths[block_index]))
        rows.append("".join(cells))
    return "\n".join(rows)


def join_vertical(position: float, *blocks: str) -> str:
    """Stack *blocks* on top of one another, aligning them horizontally per *position*."""
    blocks = tuple(b for b in blocks if b is not None)
    if not blocks:
        return ""
    width = max(max_line_width(b) for b in blocks)
    rows: list[str] = []
    for block in blocks:
        rows.append(align_horizontal(block, width, position))
    return "\n".join(rows)


def place_horizontal(width: int, position: float, text: str, fill: str = " ") -> str:
    """Place *text* within a field of *width* cells horizontally."""
    return align_horizontal(text, width, position, fill)


def place_vertical(height: int, position: float, text: str, fill: str = " ") -> str:
    """Place *text* within a field of *height* lines vertically, filling with *fill*.

    Unlike :func:`align_vertical`, the blank lines are filled to the block's
    width so the result is a solid rectangle.
    """
    width = max_line_width(text)
    blank = fill * width if width else ""
    lines = text.split("\n")
    gap = height - len(lines)
    if gap <= 0:
        return text
    top, bottom = _split_gap(gap, position)
    return "\n".join([blank] * top + lines + [blank] * bottom)


def place(
    width: int,
    height: int,
    h_position: float,
    v_position: float,
    text: str,
    fill: str = " ",
) -> str:
    """Place *text* in a *width* x *height* box at the given position.

    The result is a solid rectangle of exactly the requested size (assuming the
    content fits), padded with *fill*. Combine this with a full-screen size to
    center content in the terminal.
    """
    horizontal = align_horizontal(text, width, h_position, fill)
    return place_vertical(height, v_position, horizontal, fill)
