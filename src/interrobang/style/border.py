"""Border definitions for boxes and tables.

A :class:`Border` is just a bundle of the box-drawing glyphs used to frame
content. The edge fields (``top``/``left``/...) and corners are used for simple
boxes; the ``middle_*`` junction fields let tables draw internal grid lines.

A handful of ready-made borders are provided as module constants (see
:data:`ROUNDED`, :data:`THICK`, etc.). Build your own by constructing a
:class:`Border` directly.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "Border",
    "NORMAL",
    "ROUNDED",
    "THICK",
    "DOUBLE",
    "BLOCK",
    "HIDDEN",
    "ASCII",
    "MARKDOWN",
]


@dataclass(frozen=True)
class Border:
    """A set of glyphs used to draw a border.

    Edge characters are repeated to fill a side; corner and junction characters
    are placed once. All fields default to a single space, so a partial border
    (for example, only ``top``) is easy to specify.
    """

    top: str = " "
    bottom: str = " "
    left: str = " "
    right: str = " "
    top_left: str = " "
    top_right: str = " "
    bottom_left: str = " "
    bottom_right: str = " "
    # Junctions, used when drawing internal grid lines (tables).
    middle_left: str = " "
    middle_right: str = " "
    middle: str = " "
    middle_top: str = " "
    middle_bottom: str = " "


#: Square corners with light single lines.
NORMAL = Border(
    top="─", bottom="─", left="│", right="│",
    top_left="┌", top_right="┐", bottom_left="└", bottom_right="┘",
    middle_left="├", middle_right="┤", middle="┼", middle_top="┬", middle_bottom="┴",
)

#: Like :data:`NORMAL` but with gently rounded corners. A great default.
ROUNDED = Border(
    top="─", bottom="─", left="│", right="│",
    top_left="╭", top_right="╮", bottom_left="╰", bottom_right="╯",
    middle_left="├", middle_right="┤", middle="┼", middle_top="┬", middle_bottom="┴",
)

#: Heavy single lines.
THICK = Border(
    top="━", bottom="━", left="┃", right="┃",
    top_left="┏", top_right="┓", bottom_left="┗", bottom_right="┛",
    middle_left="┣", middle_right="┫", middle="╋", middle_top="┳", middle_bottom="┻",
)

#: Double lines.
DOUBLE = Border(
    top="═", bottom="═", left="║", right="║",
    top_left="╔", top_right="╗", bottom_left="╚", bottom_right="╝",
    middle_left="╠", middle_right="╣", middle="╬", middle_top="╦", middle_bottom="╩",
)

#: A solid block frame.
BLOCK = Border(
    top="█", bottom="█", left="█", right="█",
    top_left="█", top_right="█", bottom_left="█", bottom_right="█",
    middle_left="█", middle_right="█", middle="█", middle_top="█", middle_bottom="█",
)

#: An invisible border made of spaces -- reserves the space without drawing.
HIDDEN = Border(
    top=" ", bottom=" ", left=" ", right=" ",
    top_left=" ", top_right=" ", bottom_left=" ", bottom_right=" ",
    middle_left=" ", middle_right=" ", middle=" ", middle_top=" ", middle_bottom=" ",
)

#: Plain ASCII, for terminals or fonts without box-drawing glyphs.
ASCII = Border(
    top="-", bottom="-", left="|", right="|",
    top_left="+", top_right="+", bottom_left="+", bottom_right="+",
    middle_left="+", middle_right="+", middle="+", middle_top="+", middle_bottom="+",
)

#: A Markdown-table style border (pipes and dashes), handy for tables.
MARKDOWN = Border(
    top="-", bottom="-", left="|", right="|",
    top_left="|", top_right="|", bottom_left="|", bottom_right="|",
    middle_left="|", middle_right="|", middle="|", middle_top="|", middle_bottom="|",
)
