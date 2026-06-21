"""Low-level ANSI escape handling and terminal cell-width measurement.

This module is the bedrock of interrobang's rendering. Terminals lay text out
on a grid of *cells*; most characters occupy one cell, but wide East-Asian
glyphs occupy two and combining marks occupy zero. Getting this right is what
lets borders line up and columns stay aligned.

Everything here is pure, side-effect free, and depends only on the standard
library (``re`` and ``unicodedata``).
"""

from __future__ import annotations

import re
import unicodedata

#: The escape character that begins every ANSI control sequence.
ESC: str = "\x1b"
#: Control Sequence Introducer (``ESC[``), the prefix for most sequences.
CSI: str = ESC + "["
#: A full reset of all SGR (Select Graphic Rendition) attributes.
RESET: str = CSI + "0m"

# A reasonably complete matcher for the escape sequences a TUI emits or reads:
#   * CSI sequences  -> colors, cursor movement, erases  (ESC [ ... final)
#   * OSC sequences  -> window titles, hyperlinks         (ESC ] ... BEL/ST)
#   * two-byte ESC   -> e.g. ESC c (reset), ESC M (reverse index)
_ANSI_RE = re.compile(
    r"""
      \x1b\[ [0-?]* [ -/]* [@-~]        # CSI: ESC [ params intermediates final
    | \x1b\] .*? (?: \x07 | \x1b\\ )    # OSC: ESC ] ... terminated by BEL or ST
    | \x1b [@-Z\\-_]                    # Fe escape: ESC + single byte
    """,
    re.VERBOSE | re.DOTALL,
)


def strip_ansi(text: str) -> str:
    """Return *text* with every ANSI escape sequence removed.

    >>> strip_ansi("\\x1b[1mbold\\x1b[0m")
    'bold'
    """
    return _ANSI_RE.sub("", text)


def char_width(char: str) -> int:
    """Return the number of terminal cells a single character occupies.

    Combining marks and control characters are zero width, wide and fullwidth
    East-Asian characters are two cells, and everything else is one. This uses
    only :mod:`unicodedata`, so it has no third-party dependencies; it is a very
    good approximation but, like every pure-Unicode heuristic, cannot perfectly
    predict every terminal's emoji handling.
    """
    if not char:
        return 0
    codepoint = ord(char[0])
    # NUL and the C0/C1 control ranges render to nothing useful.
    if codepoint == 0 or codepoint < 32 or 0x7F <= codepoint < 0xA0:
        return 0
    if unicodedata.combining(char):
        return 0
    if unicodedata.east_asian_width(char) in ("W", "F"):
        return 2
    return 1


def string_width(text: str) -> int:
    """Return the printed cell width of *text*, ignoring ANSI escapes.

    Newlines are treated as ordinary (zero-effect) characters here; callers that
    care about multi-line layout should measure line by line. Use
    :func:`max_line_width` for the width of the widest line.
    """
    stripped = strip_ansi(text)
    return sum(char_width(ch) for ch in stripped)


def max_line_width(text: str) -> int:
    """Return the cell width of the widest line in *text*."""
    return max((string_width(line) for line in text.split("\n")), default=0)


def truncate(text: str, width: int, tail: str = "") -> str:
    """Truncate *text* to at most *width* cells, preserving ANSI styling.

    If truncation occurs, *tail* (for example ``"…"``) is appended and counted
    against the width budget. Escape sequences encountered before the cut are
    kept and a final reset is emitted so styling never bleeds past the cut.
    """
    if width <= 0:
        return ""
    if string_width(text) <= width:
        return text

    tail_width = string_width(tail)
    budget = max(0, width - tail_width)

    out: list[str] = []
    used = 0
    saw_escape = False
    i = 0
    length = len(text)
    while i < length:
        match = _ANSI_RE.match(text, i)
        if match:
            out.append(match.group())
            saw_escape = True
            i = match.end()
            continue
        ch = text[i]
        w = char_width(ch)
        if used + w > budget:
            break
        out.append(ch)
        used += w
        i += 1

    result = "".join(out)
    if saw_escape:
        result += RESET
    return result + tail


def wrap(text: str, width: int) -> str:
    """Greedily word-wrap *text* to *width* cells, preserving existing newlines.

    Words longer than *width* are hard-broken. Measurement ignores ANSI escapes
    so styled words wrap by their visible width. This is intentionally simple
    (no hyphenation or locale-aware breaking) but covers the common cases.
    """
    if width <= 0:
        return text
    out_lines: list[str] = []
    for paragraph in text.split("\n"):
        if paragraph == "":
            out_lines.append("")
            continue
        line = ""
        line_w = 0
        for word in paragraph.split(" "):
            word_w = string_width(word)
            if line == "":
                # First word on the line: place it, hard-breaking if needed.
                if word_w <= width:
                    line, line_w = word, word_w
                else:
                    chunks = _hard_break(word, width)
                    out_lines.extend(chunks[:-1])
                    line, line_w = chunks[-1], string_width(chunks[-1])
            elif line_w + 1 + word_w <= width:
                line += " " + word
                line_w += 1 + word_w
            else:
                out_lines.append(line)
                if word_w <= width:
                    line, line_w = word, word_w
                else:
                    chunks = _hard_break(word, width)
                    out_lines.extend(chunks[:-1])
                    line, line_w = chunks[-1], string_width(chunks[-1])
        out_lines.append(line)
    return "\n".join(out_lines)


def _hard_break(word: str, width: int) -> list[str]:
    """Split a single over-long *word* into chunks of at most *width* cells."""
    chunks: list[str] = []
    current = ""
    current_w = 0
    for ch in word:
        w = char_width(ch)
        if current_w + w > width and current:
            chunks.append(current)
            current, current_w = ch, w
        else:
            current += ch
            current_w += w
    chunks.append(current)
    return chunks
