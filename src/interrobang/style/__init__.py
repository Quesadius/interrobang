"""interrobang's styling engine -- the Lip Gloss analog.

Import the pieces you need from here::

    from interrobang.style import Style, Color, AdaptiveColor, ROUNDED
    from interrobang.style import join_horizontal, place, CENTER

The two stars are :class:`Style` (chainable text styling and box layout) and the
color types (:class:`Color`, :class:`AdaptiveColor`, :class:`CompleteColor`).
Borders are plain data; pick a preset such as :data:`ROUNDED` or build a
:class:`Border` yourself. Layout helpers compose rendered blocks together.
"""

from .border import (
    ASCII,
    BLOCK,
    DOUBLE,
    HIDDEN,
    MARKDOWN,
    NORMAL,
    ROUNDED,
    THICK,
    Border,
)
from .color import (
    ANSIColor,
    AdaptiveColor,
    Color,
    ColorLike,
    CompleteColor,
    NoColor,
    Profile,
    TerminalColor,
    ansi256_to_rgb,
    parse_color,
    parse_hex,
    rgb_to_ansi16,
    rgb_to_ansi256,
)
from .layout import (
    BOTTOM,
    CENTER,
    LEFT,
    RIGHT,
    TOP,
    align_horizontal,
    align_vertical,
    join_horizontal,
    join_vertical,
    place,
    place_horizontal,
    place_vertical,
)
from .style import (
    Style,
    get_color_profile,
    get_has_dark_background,
    set_color_profile,
    set_has_dark_background,
)

__all__ = [
    # style
    "Style",
    "set_color_profile",
    "get_color_profile",
    "set_has_dark_background",
    "get_has_dark_background",
    # color
    "Profile",
    "TerminalColor",
    "Color",
    "ANSIColor",
    "AdaptiveColor",
    "CompleteColor",
    "NoColor",
    "ColorLike",
    "parse_color",
    "parse_hex",
    "rgb_to_ansi256",
    "ansi256_to_rgb",
    "rgb_to_ansi16",
    # border
    "Border",
    "NORMAL",
    "ROUNDED",
    "THICK",
    "DOUBLE",
    "BLOCK",
    "HIDDEN",
    "ASCII",
    "MARKDOWN",
    # layout
    "LEFT",
    "CENTER",
    "RIGHT",
    "TOP",
    "BOTTOM",
    "align_horizontal",
    "align_vertical",
    "join_horizontal",
    "join_vertical",
    "place",
    "place_horizontal",
    "place_vertical",
]
