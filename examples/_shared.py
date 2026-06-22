"""Shared helper for the examples: a ``--theme`` command-line flag.

Run any interactive example with ``--theme`` to switch palettes::

    python examples/dashboard.py --theme solarized-light
    python examples/list.py --theme charm
    python examples/spinner.py --theme=solarized-dark

This module is a helper, not an example itself (the leading underscore keeps it
out of the example test sweep).
"""

from __future__ import annotations

import sys

from interrobang import CHARM, SOLARIZED_DARK, SOLARIZED_LIGHT, Theme, set_theme

THEMES: dict[str, Theme] = {
    "solarized-dark": SOLARIZED_DARK,
    "solarized-light": SOLARIZED_LIGHT,
    "charm": CHARM,
}


def apply_theme_flag(argv: list[str] | None = None) -> Theme | None:
    """Read ``--theme NAME`` (or ``--theme=NAME``) from *argv* and set that theme.

    Returns the chosen theme, or ``None`` if no flag was given. Exits with a
    helpful message on an unknown theme name.
    """
    args = sys.argv[1:] if argv is None else list(argv)
    name: str | None = None
    for i, arg in enumerate(args):
        if arg == "--theme" and i + 1 < len(args):
            name = args[i + 1]
        elif arg.startswith("--theme="):
            name = arg.split("=", 1)[1]
    if name is None:
        return None

    key = name.strip().lower().replace("_", "-")
    theme = THEMES.get(key)
    if theme is None:
        valid = ", ".join(sorted(THEMES))
        print(f"unknown theme {name!r}; choose from: {valid}", file=sys.stderr)
        sys.exit(2)
    set_theme(theme)
    return theme
