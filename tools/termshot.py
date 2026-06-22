"""Render ANSI terminal output to a self-contained SVG "screenshot".

This is a small, dependency-free ANSI-to-SVG converter used to generate the
images in the documentation. It parses the SGR (color/attribute) escape codes
that ``Style.render`` and the components emit, lays the text out on a cell grid
(using interrobang's own cell-width measurement, so wide characters and borders
align), and draws it inside a terminal-window frame.

Two entry points:

* :func:`render_svg` — a single still frame.
* :func:`render_animated_svg` — multiple frames cycled with SMIL animation, for
  the spinner and progress bar. (Animates in browsers; still renderers show the
  first frame.)

Run ``python tools/generate_images.py`` to regenerate every documentation image.
"""

from __future__ import annotations

import re

from interrobang._ansi import char_width, string_width
from interrobang.style.color import ansi256_to_rgb

# --- terminal theme -----------------------------------------------------------

BG = "#16161e"
TITLEBAR = "#22232f"
FG = "#c0caf5"
TITLE_FG = "#7f849c"
TRAFFIC = ("#ff5f56", "#febc2e", "#28c840")

FONT = (
    "'SFMono-Regular', 'JetBrains Mono', 'Fira Code', 'Cascadia Code', "
    "Menlo, Consolas, 'DejaVu Sans Mono', monospace"
)

# Cell metrics (px). Text is positioned per-cell and stretched with textLength,
# so alignment holds regardless of the viewer's actual monospace font.
CELL_W = 8.4
LINE_H = 18.0
FONT_SIZE = 13.5
PAD_X = 16.0
PAD_Y = 14.0
TITLEBAR_H = 34.0
RADIUS = 9.0

_SGR_RE = re.compile(r"\x1b\[([0-9;]*)m")


def _default_state() -> dict:
    return {
        "fg": None,
        "bg": None,
        "bold": False,
        "faint": False,
        "italic": False,
        "underline": False,
        "reverse": False,
        "strike": False,
    }


def _apply_sgr(state: dict, params: str) -> None:
    codes = [int(p) if p else 0 for p in params.split(";")]
    i = 0
    while i < len(codes):
        c = codes[i]
        if c == 0:
            state.update(_default_state())
        elif c == 1:
            state["bold"] = True
        elif c == 2:
            state["faint"] = True
        elif c == 3:
            state["italic"] = True
        elif c == 4:
            state["underline"] = True
        elif c == 7:
            state["reverse"] = True
        elif c == 9:
            state["strike"] = True
        elif c == 22:
            state["bold"] = state["faint"] = False
        elif c == 23:
            state["italic"] = False
        elif c == 24:
            state["underline"] = False
        elif c == 27:
            state["reverse"] = False
        elif c == 29:
            state["strike"] = False
        elif 30 <= c <= 37:
            state["fg"] = ansi256_to_rgb(c - 30)
        elif 90 <= c <= 97:
            state["fg"] = ansi256_to_rgb(c - 90 + 8)
        elif 40 <= c <= 47:
            state["bg"] = ansi256_to_rgb(c - 40)
        elif 100 <= c <= 107:
            state["bg"] = ansi256_to_rgb(c - 100 + 8)
        elif c == 39:
            state["fg"] = None
        elif c == 49:
            state["bg"] = None
        elif c in (38, 48):
            target = "fg" if c == 38 else "bg"
            mode = codes[i + 1] if i + 1 < len(codes) else 0
            if mode == 5 and i + 2 < len(codes):
                state[target] = ansi256_to_rgb(codes[i + 2])
                i += 2
            elif mode == 2 and i + 4 < len(codes):
                state[target] = (codes[i + 2], codes[i + 3], codes[i + 4])
                i += 4
        i += 1


def _tokenize(line: str) -> list[tuple[str, dict]]:
    """Split a line into (text, style) runs, applying SGR codes as they appear."""
    runs: list[tuple[str, dict]] = []
    state = _default_state()
    pos = 0
    for m in _SGR_RE.finditer(line):
        if m.start() > pos:
            runs.append((line[pos:m.start()], dict(state)))
        _apply_sgr(state, m.group(1))
        pos = m.end()
    if pos < len(line):
        runs.append((line[pos:], dict(state)))
    return runs


def _rgb(value) -> str:
    return "#%02x%02x%02x" % value


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _effective_colors(state: dict) -> tuple[str, str | None]:
    fg = state["fg"]
    bg = state["bg"]
    if state["reverse"]:
        new_fg = _rgb(bg) if bg else BG
        new_bg = _rgb(fg) if fg else FG
        return new_fg, new_bg
    return (_rgb(fg) if fg else FG), (_rgb(bg) if bg else None)


def _render_content(ansi: str, top: float) -> tuple[list[str], int, int]:
    """Render text content to SVG fragments. Returns (fragments, cols, rows)."""
    lines = ansi.split("\n")
    cols = max((string_width(line) for line in lines), default=0)
    parts: list[str] = []
    for row, line in enumerate(lines):
        line_top = top + row * LINE_H
        baseline = line_top + FONT_SIZE + 1.5
        cell = 0
        spans: list[str] = []
        for text, state in _tokenize(line):
            width = string_width(text)
            if width == 0:
                continue
            x = PAD_X + cell * CELL_W
            fg, bg = _effective_colors(state)
            if bg is not None:
                parts.append(
                    f'<rect x="{x:.1f}" y="{line_top:.1f}" '
                    f'width="{width * CELL_W:.1f}" height="{LINE_H:.1f}" fill="{bg}"/>'
                )
            attrs = [f'x="{x:.1f}"', f'textLength="{width * CELL_W:.1f}"', f'fill="{fg}"']
            if state["bold"]:
                attrs.append('font-weight="bold"')
            if state["italic"]:
                attrs.append('font-style="italic"')
            if state["underline"] or state["strike"]:
                deco = "underline" if state["underline"] else "line-through"
                attrs.append(f'text-decoration="{deco}"')
            if state["faint"]:
                attrs.append('opacity="0.55"')
            spans.append(f'<tspan {" ".join(attrs)}>{_escape(text)}</tspan>')
            cell += width
        if spans:
            parts.append(
                f'<text y="{baseline:.1f}" xml:space="preserve">{"".join(spans)}</text>'
            )
    return parts, cols, len(lines)


def _frame(cols: int, rows: int, title: str) -> tuple[float, float, list[str]]:
    width = round(cols * CELL_W + 2 * PAD_X)
    height = round(TITLEBAR_H + rows * LINE_H + 2 * PAD_Y)
    chrome = [
        f'<rect x="0" y="0" width="{width}" height="{height}" rx="{RADIUS}" fill="{BG}"/>',
        f'<path d="M0 {RADIUS} Q0 0 {RADIUS} 0 H{width - RADIUS} Q{width} 0 {width} {RADIUS} '
        f'V{TITLEBAR_H:.0f} H0 Z" fill="{TITLEBAR}"/>',
    ]
    for i, color in enumerate(TRAFFIC):
        chrome.append(f'<circle cx="{18 + i * 20}" cy="{TITLEBAR_H / 2:.0f}" r="6" fill="{color}"/>')
    if title:
        chrome.append(
            f'<text x="{width / 2:.0f}" y="{TITLEBAR_H / 2 + 4:.0f}" text-anchor="middle" '
            f'fill="{TITLE_FG}" font-size="12">{_escape(title)}</text>'
        )
    return width, height, chrome


def _svg_open(width: float, height: float) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="{FONT}" font-size="{FONT_SIZE}">'
    )


def render_svg(ansi: str, title: str = "") -> str:
    """Render a single ANSI block to an SVG terminal screenshot."""
    content, cols, rows = _render_content(ansi, TITLEBAR_H + PAD_Y)
    width, height, chrome = _frame(cols, rows, title)
    return _svg_open(width, height) + "".join(chrome) + "".join(content) + "</svg>"


def render_animated_svg(frames: list[str], title: str = "", fps: float = 6.0) -> str:
    """Render multiple ANSI frames as a looping (SMIL-animated) SVG."""
    n = len(frames)
    cols = max(string_width(line) for frame in frames for line in frame.split("\n"))
    rows = max(frame.count("\n") + 1 for frame in frames)
    width, height, chrome = _frame(cols, rows, title)
    dur = n / fps
    key_times = ",".join(f"{k / n:.4f}" for k in range(n))

    groups: list[str] = []
    for i, frame in enumerate(frames):
        content, _, _ = _render_content(frame, TITLEBAR_H + PAD_Y)
        values = ";".join("1" if k == i else "0" for k in range(n))
        animate = (
            f'<animate attributeName="opacity" calcMode="discrete" '
            f'values="{values}" keyTimes="{key_times}" dur="{dur:.3f}s" '
            f'repeatCount="indefinite"/>'
        )
        opacity = "1" if i == 0 else "0"
        groups.append(f'<g opacity="{opacity}">{animate}{"".join(content)}</g>')

    return _svg_open(width, height) + "".join(chrome) + "".join(groups) + "</svg>"
