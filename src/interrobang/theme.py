"""Themes -- named color palettes that components draw their defaults from.

A :class:`Theme` is a bundle of semantic colors (a primary accent, a selection
color, muted text, gradient endpoints, ...). Components read the *active* theme
when constructed and colour their default styles accordingly, so switching the
whole app's look is one call::

    import interrobang as irb
    irb.set_theme(irb.CHARM)        # or irb.SOLARIZED_DARK (the default)

interrobang ships two themes: :data:`SOLARIZED_DARK` (the default) and
:data:`CHARM`. Build your own by constructing a :class:`Theme` -- every field is
a color string (hex like ``"#268bd2"`` or a palette index like ``"5"``).

Themes affect component *accents* (titles, selections, borders, progress, hints)
-- body text keeps using the terminal's own foreground so apps look right
whatever the user's actual terminal colors are. The ``background``/``surface``/
``text`` fields describe the intended terminal look and are used by the docs
screenshot tooling; an app may also use them to paint its own backdrop.
"""

from __future__ import annotations

import weakref
from dataclasses import dataclass

__all__ = [
    "Theme",
    "SOLARIZED_DARK",
    "SOLARIZED_LIGHT",
    "CHARM",
    "set_theme",
    "get_theme",
    "register_themed",
]


@dataclass(frozen=True)
class Theme:
    """A named palette of semantic colors used for component defaults."""

    name: str
    # Intended terminal surfaces (used by the screenshot tooling / optional app backdrops).
    background: str
    surface: str
    text: str
    # Accents.
    primary: str  #: Headers, titles, directory names, the main accent.
    secondary: str  #: Default panel border color.
    selection: str  #: Highlighted/selected items.
    on_primary: str  #: Text shown on a ``primary``-colored background.
    on_selection: str  #: Text shown on a ``selection``-colored background.
    bright: str  #: Emphasized text (e.g. table headers).
    muted: str  #: Secondary text: descriptions, status lines, help text.
    subtle: str  #: Tertiary text: help keys.
    faint: str  #: Most-dimmed: help separators.
    gradient_start: str  #: Progress-bar gradient start.
    gradient_end: str  #: Progress-bar gradient end.


#: The default theme. Ethan Schoonover's Solarized Dark.
SOLARIZED_DARK = Theme(
    name="Solarized Dark",
    background="#002b36",  # base03
    surface="#073642",  # base02
    text="#839496",  # base0
    primary="#268bd2",  # blue
    secondary="#6c71c4",  # violet
    selection="#d33682",  # magenta
    on_primary="#fdf6e3",  # base3
    on_selection="#002b36",  # base03
    bright="#93a1a1",  # base1
    muted="#657b83",  # base00
    subtle="#93a1a1",  # base1
    faint="#586e75",  # base01
    gradient_start="#268bd2",  # blue
    gradient_end="#859900",  # green
)

#: Solarized Light -- the same accents on Schoonover's light base.
SOLARIZED_LIGHT = Theme(
    name="Solarized Light",
    background="#fdf6e3",  # base3
    surface="#eee8d5",  # base2
    text="#657b83",  # base00
    primary="#268bd2",  # blue
    secondary="#6c71c4",  # violet
    selection="#d33682",  # magenta
    on_primary="#fdf6e3",  # base3
    on_selection="#fdf6e3",  # base3
    bright="#586e75",  # base01 (dark emphasis on a light background)
    muted="#93a1a1",  # base1
    subtle="#586e75",  # base01
    faint="#eee8d5",  # base2
    gradient_start="#268bd2",  # blue
    gradient_end="#859900",  # green
)

#: The look interrobang shipped with originally, inspired by Charm's palette.
CHARM = Theme(
    name="Charm",
    background="#16161e",
    surface="#22232f",
    text="#c0caf5",
    primary="#7D56F4",
    secondary="#5f5fff",
    selection="#EE6FF8",
    on_primary="#FAFAFA",
    on_selection="#1A1A1A",
    bright="#FAFAFA",
    muted="#8a8a8a",
    subtle="#909090",
    faint="#3c3c3c",
    gradient_start="#FF7CCB",
    gradient_end="#FDFF8C",
)

_active_theme: Theme = SOLARIZED_DARK

# Live, theme-aware components register here (weakly, so they can be GC'd) so
# that changing the theme re-styles everything currently on screen.
_themed: "weakref.WeakSet" = weakref.WeakSet()


def register_themed(component: object) -> None:
    """Register a component to be re-styled whenever the theme changes.

    The component must expose ``_apply_theme(theme)``. Components do this for
    themselves on construction; you rarely need to call it directly.
    """
    _themed.add(component)


def set_theme(theme: Theme) -> None:
    """Set the active theme and re-style every live component.

    Components built afterwards use the new colors, and any already-constructed
    component that registered itself is re-styled in place -- so switching the
    theme updates what's already on screen. This resets theme-derived styles to
    the new theme's defaults, so apply custom style overrides *after*
    ``set_theme`` if you mix the two.
    """
    global _active_theme
    _active_theme = theme
    for component in list(_themed):
        apply = getattr(component, "_apply_theme", None)
        if apply is not None:
            apply(theme)


def get_theme() -> Theme:
    """Return the active theme."""
    return _active_theme
