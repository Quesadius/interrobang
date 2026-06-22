"""A filesystem browser for choosing a file or directory.

Navigate with the arrow keys, descend into a directory or select a file with
Enter, and go back up with Backspace/Left. After each :meth:`FilePicker.update`,
check :meth:`FilePicker.did_select_file`::

    picker = FilePicker(path="~/Documents", height=15)
    picker, cmd = picker.update(msg)
    chosen = picker.did_select_file()
    if chosen:
        ...

The component reads the filesystem in ``view``/``update`` via :mod:`os`, so it
is the one component with side effects -- harmless ones (listing directories).
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from ..key import KeyMsg
from ..style import Color, Style
from ..theme import get_theme

__all__ = ["FileEntry", "FilePicker"]


@dataclass
class FileEntry:
    """One row in the picker: a name, full path, and whether it is a directory."""

    name: str
    path: str
    is_dir: bool


class FilePicker:
    """Browse the filesystem and pick a file or directory."""

    def __init__(self, path: str = ".", height: int = 15):
        self.current_dir = os.path.abspath(os.path.expanduser(path))
        self.height = height
        self.cursor = 0
        self.offset = 0
        self.show_hidden = False
        self.dir_allowed = False  # allow selecting directories with Enter
        self.file_allowed = True
        self._selected: str | None = None

        self.cursor_prefix = "> "
        self.normal_prefix = "  "
        theme = get_theme()
        self.dir_style = Style().foreground(theme.primary).bold()
        self.file_style = Style()
        self.selected_style = Style().foreground(theme.selection).bold()
        self.path_style = Style().foreground(theme.muted)

    # -- listing -----------------------------------------------------------

    def read_dir(self) -> list[FileEntry]:
        """List the current directory: directories first, then files, sorted."""
        try:
            names = os.listdir(self.current_dir)
        except OSError:
            return []
        entries: list[FileEntry] = []
        for name in names:
            if not self.show_hidden and name.startswith("."):
                continue
            full = os.path.join(self.current_dir, name)
            entries.append(FileEntry(name, full, os.path.isdir(full)))
        entries.sort(key=lambda e: (not e.is_dir, e.name.lower()))
        return entries

    # -- selection ---------------------------------------------------------

    def did_select_file(self) -> str | None:
        """Return the path chosen since the last call, then clear it."""
        chosen = self._selected
        self._selected = None
        return chosen

    def _go_up(self) -> None:
        parent = os.path.dirname(self.current_dir)
        if parent and parent != self.current_dir:
            self.current_dir = parent
            self.cursor = 0
            self.offset = 0

    def _enter(self, entries: list[FileEntry]) -> None:
        if not entries or self.cursor >= len(entries):
            return
        entry = entries[self.cursor]
        if entry.is_dir:
            if self.dir_allowed:
                self._selected = entry.path
            else:
                self.current_dir = entry.path
                self.cursor = 0
                self.offset = 0
        elif self.file_allowed:
            self._selected = entry.path

    # -- update ------------------------------------------------------------

    def update(self, msg: object) -> "tuple[FilePicker, None]":
        if not isinstance(msg, KeyMsg):
            return self, None
        entries = self.read_dir()
        key = msg.key
        if key in ("up", "k"):
            if self.cursor > 0:
                self.cursor -= 1
                if self.cursor < self.offset:
                    self.offset = self.cursor
        elif key in ("down", "j"):
            if self.cursor < len(entries) - 1:
                self.cursor += 1
                if self.cursor >= self.offset + self.height:
                    self.offset = self.cursor - self.height + 1
        elif key in ("enter", "right", "l"):
            self._enter(entries)
        elif key in ("backspace", "left", "h"):
            self._go_up()
        elif key == ".":
            self.show_hidden = not self.show_hidden
            self.cursor = 0
            self.offset = 0
        return self, None

    # -- view --------------------------------------------------------------

    def view(self) -> str:
        entries = self.read_dir()
        lines = [self.path_style.render(self.current_dir)]
        window = entries[self.offset : self.offset + self.height]
        if not window:
            lines.append(self.path_style.render("  (empty)"))
        for i, entry in enumerate(window):
            index = self.offset + i
            selected = index == self.cursor
            prefix = self.cursor_prefix if selected else self.normal_prefix
            name = entry.name + ("/" if entry.is_dir else "")
            if selected:
                style = self.selected_style
            elif entry.is_dir:
                style = self.dir_style
            else:
                style = self.file_style
            lines.append(prefix + style.render(name))
        return "\n".join(lines)
