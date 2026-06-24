"""The :class:`Style` -- a chainable, immutable description of how text looks.

A style bundles text attributes (bold, italic, ...), colors, sizing, padding,
margins, alignment, and an optional border. You build one up with fluent
setters, each of which returns a *new* style, and then call :meth:`Style.render`
to turn text into an ANSI-decorated string::

    from interrobang.style import Style, Color, ROUNDED

    box = (
        Style()
        .bold()
        .foreground(Color("#FAFAFA"))
        .background(Color("#7D56F4"))
        .padding(1, 3)
        .border(ROUNDED)
    )
    print(box.render("Hello, there!"))

Because styles are immutable, they are safe to define once at module scope and
reuse everywhere.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field, replace
from typing import Callable, Optional

from .._ansi import CSI, RESET, max_line_width, truncate, wrap
from . import border as _border_mod
from .border import Border
from .color import ColorLike, Profile, TerminalColor, parse_color
from .layout import LEFT, TOP, align_horizontal

__all__ = [
    "Style",
    "set_color_profile",
    "get_color_profile",
    "set_has_dark_background",
    "get_has_dark_background",
]

# Module-wide rendering defaults. The runtime updates these after detecting the
# terminal's capabilities; standalone use gets sensible, capable defaults.
_DEFAULT_PROFILE = Profile.TRUECOLOR
_DEFAULT_DARK = True


def set_color_profile(profile: Profile) -> None:
    """Set the default color profile used when rendering styles."""
    global _DEFAULT_PROFILE
    _DEFAULT_PROFILE = profile


def get_color_profile() -> Profile:
    """Return the current default color profile."""
    return _DEFAULT_PROFILE


def set_has_dark_background(dark: bool) -> None:
    """Tell the style engine whether the terminal background is dark."""
    global _DEFAULT_DARK
    _DEFAULT_DARK = dark


def get_has_dark_background() -> bool:
    """Return whether the terminal background is considered dark."""
    return _DEFAULT_DARK


def _expand_edges(values: tuple[int, ...]) -> tuple[int, int, int, int]:
    """Expand CSS-style edge shorthand into ``(top, right, bottom, left)``."""
    if len(values) == 1:
        v = values[0]
        return (v, v, v, v)
    if len(values) == 2:
        vertical, horizontal = values
        return (vertical, horizontal, vertical, horizontal)
    if len(values) == 3:
        top, horizontal, bottom = values
        return (top, horizontal, bottom, horizontal)
    if len(values) == 4:
        return (values[0], values[1], values[2], values[3])
    raise ValueError("edges take 1, 2, 3, or 4 values (CSS order)")


def _apply_seq(text: str, seq: str) -> str:
    """Wrap *text* in an SGR sequence, re-applying it after any inner resets.

    Re-applying after ``RESET`` means a styled block (say, a purple background)
    survives spans of nested styling inside it instead of being cleared midway.
    """
    if not seq:
        return text
    return seq + text.replace(RESET, RESET + seq) + RESET


@dataclass(frozen=True)
class Style:
    """An immutable bundle of visual attributes; see the module docstring."""

    _bold: bool = False
    _faint: bool = False
    _italic: bool = False
    _underline: bool = False
    _strikethrough: bool = False
    _blink: bool = False
    _reverse: bool = False
    _foreground: Optional[TerminalColor] = None
    _background: Optional[TerminalColor] = None
    _width: Optional[int] = None
    _height: Optional[int] = None
    _max_width: Optional[int] = None
    _max_height: Optional[int] = None
    _align_h: float = LEFT
    _align_v: float = TOP
    _padding: tuple[int, int, int, int] = (0, 0, 0, 0)
    _margin: tuple[int, int, int, int] = (0, 0, 0, 0)
    _margin_bg: Optional[TerminalColor] = None
    _border: Optional[Border] = None
    _border_sides: tuple[bool, bool, bool, bool] = (True, True, True, True)
    _border_fg: Optional[TerminalColor] = None
    _border_bg: Optional[TerminalColor] = None
    _inline: bool = False
    _transform: Optional[Callable[[str], str]] = field(default=None, compare=False)
    _profile: Optional[Profile] = None
    _dark: Optional[bool] = None

    # -- text attributes ---------------------------------------------------

    def bold(self, value: bool = True) -> "Style":
        """Return a copy with bold turned on (or off)."""
        return replace(self, _bold=value)

    def faint(self, value: bool = True) -> "Style":
        """Return a copy with faint/dim turned on (or off)."""
        return replace(self, _faint=value)

    def italic(self, value: bool = True) -> "Style":
        """Return a copy with italics turned on (or off)."""
        return replace(self, _italic=value)

    def underline(self, value: bool = True) -> "Style":
        """Return a copy with underline turned on (or off)."""
        return replace(self, _underline=value)

    def strikethrough(self, value: bool = True) -> "Style":
        """Return a copy with strikethrough turned on (or off)."""
        return replace(self, _strikethrough=value)

    def blink(self, value: bool = True) -> "Style":
        """Return a copy with blink turned on (or off)."""
        return replace(self, _blink=value)

    def reverse(self, value: bool = True) -> "Style":
        """Return a copy with reverse-video turned on (or off)."""
        return replace(self, _reverse=value)

    # -- colors ------------------------------------------------------------

    def foreground(self, color: Optional[ColorLike]) -> "Style":
        """Return a copy with the foreground (text) color set."""
        return replace(self, _foreground=None if color is None else parse_color(color))

    def background(self, color: Optional[ColorLike]) -> "Style":
        """Return a copy with the background color set."""
        return replace(self, _background=None if color is None else parse_color(color))

    # -- sizing ------------------------------------------------------------

    def width(self, value: Optional[int]) -> "Style":
        """Return a copy with a fixed content width (text is wrapped to fit)."""
        return replace(self, _width=value)

    def height(self, value: Optional[int]) -> "Style":
        """Return a copy with a fixed block height (padded or cropped to fit)."""
        return replace(self, _height=value)

    def max_width(self, value: Optional[int]) -> "Style":
        """Return a copy that truncates every rendered line to *value* cells."""
        return replace(self, _max_width=value)

    def max_height(self, value: Optional[int]) -> "Style":
        """Return a copy that keeps at most *value* rendered lines."""
        return replace(self, _max_height=value)

    # -- alignment ---------------------------------------------------------

    def align(self, position: float) -> "Style":
        """Return a copy with horizontal alignment set (0=left, .5=center, 1=right)."""
        return replace(self, _align_h=position)

    align_horizontal = align

    def align_vertical(self, position: float) -> "Style":
        """Return a copy with vertical alignment set (0=top, .5=middle, 1=bottom)."""
        return replace(self, _align_v=position)

    # -- spacing -----------------------------------------------------------

    def padding(self, *values: int) -> "Style":
        """Return a copy with padding set, CSS-style (1, 2, 3, or 4 values)."""
        return replace(self, _padding=_expand_edges(values))

    def padding_top(self, n: int) -> "Style":
        t, r, b, l = self._padding
        return replace(self, _padding=(n, r, b, l))

    def padding_right(self, n: int) -> "Style":
        t, r, b, l = self._padding
        return replace(self, _padding=(t, n, b, l))

    def padding_bottom(self, n: int) -> "Style":
        t, r, b, l = self._padding
        return replace(self, _padding=(t, r, n, l))

    def padding_left(self, n: int) -> "Style":
        t, r, b, l = self._padding
        return replace(self, _padding=(t, r, b, n))

    def margin(self, *values: int) -> "Style":
        """Return a copy with margins set, CSS-style (1, 2, 3, or 4 values)."""
        return replace(self, _margin=_expand_edges(values))

    def margin_top(self, n: int) -> "Style":
        t, r, b, l = self._margin
        return replace(self, _margin=(n, r, b, l))

    def margin_right(self, n: int) -> "Style":
        t, r, b, l = self._margin
        return replace(self, _margin=(t, n, b, l))

    def margin_bottom(self, n: int) -> "Style":
        t, r, b, l = self._margin
        return replace(self, _margin=(t, r, n, l))

    def margin_left(self, n: int) -> "Style":
        t, r, b, l = self._margin
        return replace(self, _margin=(t, r, b, n))

    def margin_background(self, color: Optional[ColorLike]) -> "Style":
        """Return a copy that fills the margin area with a background color."""
        return replace(self, _margin_bg=None if color is None else parse_color(color))

    # -- border ------------------------------------------------------------

    def border(
        self,
        border: Optional[Border] = None,
        top: bool = True,
        right: bool = True,
        bottom: bool = True,
        left: bool = True,
    ) -> "Style":
        """Return a copy with a border. Pass per-side flags to draw partial frames.

        With no argument, a normal single-line border is applied.
        """
        if border is None:
            border = _border_mod.NORMAL
        return replace(self, _border=border, _border_sides=(top, right, bottom, left))

    def border_foreground(self, color: Optional[ColorLike]) -> "Style":
        """Return a copy with the border's foreground color set."""
        return replace(self, _border_fg=None if color is None else parse_color(color))

    def border_background(self, color: Optional[ColorLike]) -> "Style":
        """Return a copy with the border's background color set."""
        return replace(self, _border_bg=None if color is None else parse_color(color))

    # -- misc --------------------------------------------------------------

    def inline(self, value: bool = True) -> "Style":
        """Return a copy that renders on a single line, ignoring block layout.

        Width, height, padding, margins, and borders are skipped; only text
        attributes and colors apply. Useful for styling spans within a line.
        """
        return replace(self, _inline=value)

    def transform(self, fn: Optional[Callable[[str], str]]) -> "Style":
        """Return a copy that runs *fn* over the text before styling it."""
        return replace(self, _transform=fn)

    def color_profile(self, profile: Optional[Profile]) -> "Style":
        """Return a copy pinned to a specific color profile (overrides the default)."""
        return replace(self, _profile=profile)

    def dark_background(self, value: Optional[bool]) -> "Style":
        """Return a copy that treats the background as dark/light for adaptive colors."""
        return replace(self, _dark=value)

    def copy(self) -> "Style":
        """Return an identical copy (styles are immutable, so this rarely matters)."""
        return replace(self)

    def inherit(self, other: "Style") -> "Style":
        """Return a copy that takes unset text attributes/colors/border from *other*.

        Sizing, padding, and margins are intentionally not inherited: those
        describe a specific layout, not a reusable look.
        """
        base = Style()
        changes: dict = {}
        inheritable = (
            "_bold", "_faint", "_italic", "_underline", "_strikethrough",
            "_blink", "_reverse", "_foreground", "_background",
            "_border", "_border_sides", "_border_fg", "_border_bg",
        )
        for name in inheritable:
            mine = getattr(self, name)
            if mine == getattr(base, name):  # unset on me -> take theirs
                changes[name] = getattr(other, name)
        return replace(self, **changes)

    # -- getters -----------------------------------------------------------

    def get_width(self) -> Optional[int]:
        return self._width

    def get_height(self) -> Optional[int]:
        return self._height

    def get_padding(self) -> tuple[int, int, int, int]:
        return self._padding

    def get_margin(self) -> tuple[int, int, int, int]:
        return self._margin

    def horizontal_padding(self) -> int:
        return self._padding[1] + self._padding[3]

    def vertical_padding(self) -> int:
        return self._padding[0] + self._padding[2]

    def horizontal_frame_size(self) -> int:
        """Total non-content horizontal width: padding + border + margin."""
        size = self.horizontal_padding() + self._margin[1] + self._margin[3]
        if self._border is not None:
            size += (1 if self._border_sides[3] else 0) + (1 if self._border_sides[1] else 0)
        return size

    def vertical_frame_size(self) -> int:
        """Total non-content vertical height: padding + border + margin."""
        size = self.vertical_padding() + self._margin[0] + self._margin[2]
        if self._border is not None:
            size += (1 if self._border_sides[0] else 0) + (1 if self._border_sides[2] else 0)
        return size

    # -- rendering ---------------------------------------------------------

    def _sgr(self, profile: Profile, dark: bool) -> str:
        """Build the SGR escape sequence for text attributes and colors."""
        params: list[str] = []
        if self._bold:
            params.append("1")
        if self._faint:
            params.append("2")
        if self._italic:
            params.append("3")
        if self._underline:
            params.append("4")
        if self._blink:
            params.append("5")
        if self._reverse:
            params.append("7")
        if self._strikethrough:
            params.append("9")
        if self._foreground is not None:
            seq = self._foreground.sequence(profile, dark, background=False)
            if seq:
                params.append(seq)
        if self._background is not None:
            seq = self._background.sequence(profile, dark, background=True)
            if seq:
                params.append(seq)
        if not params:
            return ""
        return CSI + ";".join(params) + "m"

    def _border_sgr(self, profile: Profile, dark: bool) -> str:
        params: list[str] = []
        if self._border_fg is not None:
            seq = self._border_fg.sequence(profile, dark, background=False)
            if seq:
                params.append(seq)
        if self._border_bg is not None:
            seq = self._border_bg.sequence(profile, dark, background=True)
            if seq:
                params.append(seq)
        if not params:
            return ""
        return CSI + ";".join(params) + "m"

    def render(self, *parts: object) -> str:
        """Render *parts* (joined by spaces) into a styled, ANSI-decorated string."""
        text = " ".join(str(p) for p in parts)
        profile = self._profile if self._profile is not None else _DEFAULT_PROFILE
        dark = self._dark if self._dark is not None else _DEFAULT_DARK

        if self._transform is not None:
            text = self._transform(text)

        seq = self._sgr(profile, dark)

        if self._inline:
            return self._apply_max(_apply_seq(text.replace("\n", ""), seq))

        pt, pr, pb, pl = self._padding

        if self._width is not None:
            inner_width = max(0, self._width - pl - pr)
            text = wrap(text, inner_width) if inner_width else ""
        else:
            inner_width = max_line_width(text)

        lines = align_horizontal(text, inner_width, self._align_h).split("\n")

        if pl or pr:
            lines = [(" " * pl) + line + (" " * pr) for line in lines]
        full_width = inner_width + pl + pr

        if pt:
            lines = [" " * full_width] * pt + lines
        if pb:
            lines = lines + [" " * full_width] * pb

        if seq:
            lines = [_apply_seq(line, seq) for line in lines]

        if self._height is not None:
            lines = self._fit_height(lines, full_width, seq)

        block = "\n".join(lines)

        if self._border is not None:
            block = self._draw_border(block, profile, dark)

        block = self._apply_margins(block, profile, dark)
        return self._apply_max(block)

    __call__ = render

    def _fit_height(self, lines: list[str], width: int, seq: str) -> list[str]:
        height = self._height or 0
        gap = height - len(lines)
        if gap == 0:
            return lines
        if gap < 0:
            return lines[:height]
        blank = _apply_seq(" " * width, seq) if seq else " " * width
        top = int(round(gap * self._align_v))
        bottom = gap - top
        return [blank] * top + lines + [blank] * bottom

    def _draw_border(self, block: str, profile: Profile, dark: bool) -> str:
        b = self._border
        assert b is not None
        top, right, bottom, left = self._border_sides
        lines = block.split("\n")
        width = max_line_width(block)
        bseq = self._border_sgr(profile, dark)

        def color(s: str) -> str:
            return _apply_seq(s, bseq) if bseq else s

        out: list[str] = []
        if top:
            tl = b.top_left if left else ""
            tr = b.top_right if right else ""
            out.append(color(tl + b.top * width + tr))
        left_edge = color(b.left) if left else ""
        right_edge = color(b.right) if right else ""
        for line in lines:
            out.append(left_edge + line + right_edge)
        if bottom:
            bl = b.bottom_left if left else ""
            br = b.bottom_right if right else ""
            out.append(color(bl + b.bottom * width + br))
        return "\n".join(out)

    def _apply_margins(self, block: str, profile: Profile, dark: bool) -> str:
        mt, mr, mb, ml = self._margin
        if not (mt or mr or mb or ml):
            return block
        lines = block.split("\n")
        width = max_line_width(block)
        mseq = ""
        if self._margin_bg is not None:
            seq = self._margin_bg.sequence(profile, dark, background=True)
            if seq:
                mseq = CSI + seq + "m"

        def fill(n: int) -> str:
            if n <= 0:
                return ""
            return _apply_seq(" " * n, mseq) if mseq else " " * n

        total_width = ml + width + mr
        blank = fill(total_width)
        left = fill(ml)
        right = fill(mr)
        out: list[str] = []
        out.extend([blank] * mt)
        for line in lines:
            out.append(left + line + right)
        out.extend([blank] * mb)
        return "\n".join(out)

    def _apply_max(self, block: str) -> str:
        if self._max_width is not None:
            block = "\n".join(
                truncate(line, self._max_width) for line in block.split("\n")
            )
        if self._max_height is not None:
            block = "\n".join(block.split("\n")[: self._max_height])
        return block
