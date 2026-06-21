"""Key bindings and an auto-generated help view.

Describe your app's keys once as :class:`KeyBinding` objects, match incoming
keys against them, and render a help line/table for free::

    quit = KeyBinding(["q", "ctrl+c"], "q", "quit")
    up = KeyBinding(["up", "k"], "↑/k", "move up")

    def update(self, msg):
        if quit.matches(msg):
            return self, irb.quit
        ...

    help = Help()
    print(help.short_view([up, quit]))   # ↑/k move up · q quit
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..key import KeyMsg
from ..style import Color, Style
from ..style.layout import join_horizontal

__all__ = ["KeyBinding", "Help"]


@dataclass
class KeyBinding:
    """A set of keys plus the help text describing what they do."""

    keys: list[str] = field(default_factory=list)
    help_key: str = ""
    help_desc: str = ""
    enabled: bool = True

    def matches(self, msg: object) -> bool:
        """True if *msg* is a :class:`KeyMsg` for one of these (enabled) keys."""
        return self.enabled and isinstance(msg, KeyMsg) and msg.key in self.keys

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled


class Help:
    """Renders help text from a list of :class:`KeyBinding` objects."""

    def __init__(self):
        self.show_all = False
        self.separator = " · "
        self.key_style = Style().foreground(Color("#909090")).bold()
        self.desc_style = Style().foreground(Color("#626262"))
        self.separator_style = Style().foreground(Color("#3C3C3C"))
        self.column_gap = 3

    def _binding_text(self, binding: KeyBinding) -> str:
        return self.key_style.render(binding.help_key) + " " + self.desc_style.render(binding.help_desc)

    def short_view(self, bindings: list[KeyBinding]) -> str:
        """A single line of the given bindings, separated by a dot."""
        parts = [self._binding_text(b) for b in bindings if b.enabled and b.help_key]
        sep = self.separator_style.render(self.separator)
        return sep.join(parts)

    def full_view(self, columns: list[list[KeyBinding]]) -> str:
        """A multi-column help table; each inner list is one column of bindings."""
        rendered_columns: list[str] = []
        for column in columns:
            rows = [self._binding_text(b) for b in column if b.enabled and b.help_key]
            rendered_columns.append("\n".join(rows))
        gap = " " * self.column_gap
        # Interleave a gap column between each real column.
        blocks: list[str] = []
        for i, col in enumerate(rendered_columns):
            if i > 0:
                blocks.append(gap)
            blocks.append(col)
        return join_horizontal(0.0, *blocks)

    def view(self, bindings: list[KeyBinding]) -> str:
        """Short help, or (when :attr:`show_all`) a single full-help column."""
        if self.show_all:
            return self.full_view([bindings])
        return self.short_view(bindings)
