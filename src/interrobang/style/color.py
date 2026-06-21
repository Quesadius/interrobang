"""Colors and color profiles.

interrobang understands four terminal color profiles and *degrades* colors
gracefully between them: a 24-bit truecolor will be approximated by the nearest
256-color, then by the nearest of the 16 base colors, and finally dropped
entirely on a monochrome terminal. This mirrors the way Charm's Lip Gloss keeps
the same source code looking right everywhere.

Color objects are immutable and pure. Resolving a color to an escape sequence
requires a :class:`Profile` (how many colors the terminal supports) and a
``dark`` flag (whether the background is dark), both supplied by the renderer.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Union

__all__ = [
    "Profile",
    "TerminalColor",
    "NoColor",
    "Color",
    "ANSIColor",
    "AdaptiveColor",
    "CompleteColor",
    "ColorLike",
    "parse_color",
]


class Profile(IntEnum):
    """How many colors a terminal can display.

    The ordering is meaningful: a higher profile is a strict superset of the
    ones below it, so degradation only ever moves *down* this enum.
    """

    ASCII = 0  #: No color at all (monochrome).
    ANSI = 1  #: The 16 standard ANSI colors.
    ANSI256 = 2  #: The 256-color xterm palette.
    TRUECOLOR = 3  #: 24-bit RGB.


# A normalized, profile-resolved color. The renderer turns these into SGR codes.
#   ("rgb", r, g, b) | ("ansi256", n) | ("ansi", n)
_Resolved = tuple


# ---------------------------------------------------------------------------
# Conversion math
# ---------------------------------------------------------------------------

# Standard xterm RGB values for the 16 base ANSI colors.
_ANSI16_RGB: tuple[tuple[int, int, int], ...] = (
    (0x00, 0x00, 0x00), (0x80, 0x00, 0x00), (0x00, 0x80, 0x00), (0x80, 0x80, 0x00),
    (0x00, 0x00, 0x80), (0x80, 0x00, 0x80), (0x00, 0x80, 0x80), (0xC0, 0xC0, 0xC0),
    (0x80, 0x80, 0x80), (0xFF, 0x00, 0x00), (0x00, 0xFF, 0x00), (0xFF, 0xFF, 0x00),
    (0x00, 0x00, 0xFF), (0xFF, 0x00, 0xFF), (0x00, 0xFF, 0xFF), (0xFF, 0xFF, 0xFF),
)

# The six steps used by each axis of the 6x6x6 color cube (indices 16-231).
_CUBE_STEPS: tuple[int, ...] = (0, 95, 135, 175, 215, 255)


def _nearest_cube_step(value: int) -> int:
    """Return the index (0-5) of the closest 6x6x6-cube step to *value*."""
    best_index = 0
    best_distance = 256
    for index, step in enumerate(_CUBE_STEPS):
        distance = abs(step - value)
        if distance < best_distance:
            best_distance = distance
            best_index = index
    return best_index


def rgb_to_ansi256(r: int, g: int, b: int) -> int:
    """Map an RGB triple to the closest index in the 256-color palette."""
    # Candidate from the color cube.
    ri, gi, bi = _nearest_cube_step(r), _nearest_cube_step(g), _nearest_cube_step(b)
    cube_index = 16 + 36 * ri + 6 * gi + bi
    cube_rgb = (_CUBE_STEPS[ri], _CUBE_STEPS[gi], _CUBE_STEPS[bi])

    # Candidate from the 24-step grayscale ramp (indices 232-255).
    average = (r + g + b) // 3
    if average < 8:
        gray_index = 232
    elif average > 238:
        gray_index = 255
    else:
        gray_index = 232 + round((average - 8) / 10)
    gray_value = 8 + 10 * (gray_index - 232)
    gray_rgb = (gray_value, gray_value, gray_value)

    if _distance((r, g, b), cube_rgb) <= _distance((r, g, b), gray_rgb):
        return cube_index
    return gray_index


def ansi256_to_rgb(n: int) -> tuple[int, int, int]:
    """Return the RGB triple for a 256-color palette index."""
    if n < 16:
        return _ANSI16_RGB[n]
    if n < 232:
        n -= 16
        return (_CUBE_STEPS[n // 36], _CUBE_STEPS[(n // 6) % 6], _CUBE_STEPS[n % 6])
    value = 8 + 10 * (n - 232)
    return (value, value, value)


def rgb_to_ansi16(r: int, g: int, b: int) -> int:
    """Map an RGB triple to the closest of the 16 base ANSI colors."""
    best_index = 0
    best_distance = None
    for index, candidate in enumerate(_ANSI16_RGB):
        distance = _distance((r, g, b), candidate)
        if best_distance is None or distance < best_distance:
            best_distance = distance
            best_index = index
    return best_index


def _distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    """Squared Euclidean distance between two RGB triples."""
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2


def parse_hex(value: str) -> tuple[int, int, int]:
    """Parse ``#rgb`` or ``#rrggbb`` (with or without ``#``) into an RGB triple."""
    text = value.lstrip("#")
    if len(text) == 3:
        text = "".join(ch * 2 for ch in text)
    if len(text) != 6:
        raise ValueError(f"invalid hex color: {value!r}")
    try:
        return (int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16))
    except ValueError as exc:  # pragma: no cover - defensive
        raise ValueError(f"invalid hex color: {value!r}") from exc


# ---------------------------------------------------------------------------
# Color types
# ---------------------------------------------------------------------------


class TerminalColor:
    """Base class for anything that can resolve to a terminal color.

    Subclasses implement :meth:`resolve`, returning a normalized tuple or
    ``None`` (meaning "no color"). End users rarely touch this directly; they
    use :class:`Color`, :class:`AdaptiveColor`, and friends.
    """

    def resolve(self, profile: Profile, dark: bool) -> _Resolved | None:  # noqa: D102
        raise NotImplementedError

    def sequence(self, profile: Profile, dark: bool, *, background: bool) -> str:
        """Return the SGR parameter string for this color (e.g. ``"38;2;255;0;0"``).

        Returns an empty string when the color resolves to nothing (no color,
        or an ASCII profile).
        """
        resolved = self.resolve(profile, dark)
        if resolved is None:
            return ""
        kind = resolved[0]
        if kind == "rgb":
            _, r, g, b = resolved
            lead = 48 if background else 38
            return f"{lead};2;{r};{g};{b}"
        if kind == "ansi256":
            _, n = resolved
            lead = 48 if background else 38
            return f"{lead};5;{n}"
        # 16-color
        _, n = resolved
        if n < 8:
            return str((40 if background else 30) + n)
        return str((100 if background else 90) + (n - 8))


class NoColor(TerminalColor):
    """An explicit "no color", useful for unsetting an inherited color."""

    def resolve(self, profile: Profile, dark: bool) -> None:
        return None

    def __repr__(self) -> str:
        return "NoColor()"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, NoColor)

    def __hash__(self) -> int:
        return hash(NoColor)


@dataclass(frozen=True)
class Color(TerminalColor):
    """A single color from a hex string or a palette index.

    Accepts:

    * a hex string -- ``Color("#ff0066")`` or shorthand ``Color("#f06")``
    * a palette index as int or string -- ``Color(212)`` / ``Color("212")``
      (0-15 are the base ANSI colors, 16-255 the extended palette)

    The color carries its most precise form and is degraded on demand by
    :meth:`resolve` according to the active :class:`Profile`.
    """

    value: Union[str, int]

    def _rgb(self) -> tuple[int, int, int] | None:
        if isinstance(self.value, int):
            return None
        text = self.value.strip()
        if text.startswith("#") or any(c in "abcdefABCDEF" for c in text):
            # Looks like hex (has a '#' or hex-only letters).
            if text.startswith("#") or not text.isdigit():
                return parse_hex(text)
        return None

    def _index(self) -> int | None:
        if isinstance(self.value, int):
            return self.value
        text = self.value.strip()
        if text.isdigit():
            return int(text)
        return None

    def resolve(self, profile: Profile, dark: bool) -> _Resolved | None:
        if profile == Profile.ASCII:
            return None

        index = self._index()
        if index is not None:
            if not 0 <= index <= 255:
                raise ValueError(f"palette index out of range 0-255: {index}")
            if index < 16:
                if profile == Profile.ANSI:
                    return ("ansi", index)
                return ("ansi256", index)
            # Extended palette index.
            if profile == Profile.ANSI:
                r, g, b = ansi256_to_rgb(index)
                return ("ansi", rgb_to_ansi16(r, g, b))
            return ("ansi256", index)

        rgb = self._rgb()
        if rgb is None:  # pragma: no cover - defensive
            raise ValueError(f"invalid color: {self.value!r}")
        r, g, b = rgb
        if profile == Profile.TRUECOLOR:
            return ("rgb", r, g, b)
        if profile == Profile.ANSI256:
            return ("ansi256", rgb_to_ansi256(r, g, b))
        return ("ansi", rgb_to_ansi16(r, g, b))

    @classmethod
    def from_rgb(cls, r: int, g: int, b: int) -> "Color":
        """Construct a :class:`Color` from individual RGB components."""
        return cls(f"#{r:02x}{g:02x}{b:02x}")


@dataclass(frozen=True)
class ANSIColor(TerminalColor):
    """One of the 16 base ANSI colors, selected explicitly by index (0-15)."""

    index: int

    def __post_init__(self) -> None:
        if not 0 <= self.index <= 15:
            raise ValueError(f"ANSIColor index must be 0-15, got {self.index}")

    def resolve(self, profile: Profile, dark: bool) -> _Resolved | None:
        if profile == Profile.ASCII:
            return None
        if profile == Profile.ANSI:
            return ("ansi", self.index)
        return ("ansi256", self.index)


@dataclass(frozen=True)
class AdaptiveColor(TerminalColor):
    """A color that adapts to the terminal background.

    ``light`` is used on light backgrounds and ``dark`` on dark backgrounds.
    Each may be any :data:`ColorLike` (hex string, index, or color object).
    """

    light: "ColorLike"
    dark: "ColorLike"

    def resolve(self, profile: Profile, dark: bool) -> _Resolved | None:
        chosen = self.dark if dark else self.light
        return parse_color(chosen).resolve(profile, dark)


@dataclass(frozen=True)
class CompleteColor(TerminalColor):
    """An exact color specified separately for each profile.

    Use this when automatic degradation does not give you the precise palette
    entry you want. Any field left as ``None`` falls back to degrading from the
    most precise field that *is* set.
    """

    true_color: str | None = None
    ansi256: int | None = None
    ansi: int | None = None

    def resolve(self, profile: Profile, dark: bool) -> _Resolved | None:
        if profile == Profile.ASCII:
            return None
        if profile == Profile.TRUECOLOR and self.true_color is not None:
            return Color(self.true_color).resolve(profile, dark)
        if profile >= Profile.ANSI256 and self.ansi256 is not None:
            return ("ansi256", self.ansi256)
        if self.ansi is not None:
            if profile == Profile.ANSI:
                return ("ansi", self.ansi)
            return ("ansi256", self.ansi)
        # Fall back to whatever precise value we do have, degraded normally.
        if self.true_color is not None:
            return Color(self.true_color).resolve(profile, dark)
        if self.ansi256 is not None:
            return Color(self.ansi256).resolve(profile, dark)
        return None


#: Anything acceptable where a color is expected.
ColorLike = Union[str, int, TerminalColor]


def parse_color(value: "ColorLike") -> TerminalColor:
    """Coerce a :data:`ColorLike` into a :class:`TerminalColor`.

    Strings and ints become :class:`Color`; existing color objects pass through.
    """
    if isinstance(value, TerminalColor):
        return value
    return Color(value)
