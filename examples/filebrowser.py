"""A two-pane file browser: navigate on the left, preview on the right.

    python examples/filebrowser.py [start-dir]

↑/↓ move · Enter opens a directory · Backspace goes up · ``.`` toggles hidden
files · PgUp/PgDn scroll the preview · q quits. Shows how a couple of components
(FilePicker + Viewport) compose with the layout helpers into a real tool.
"""

import os
import sys

from interrobang import KeyMsg, WindowSizeMsg, get_theme, quit
from interrobang.components import FilePicker, Viewport
from interrobang.style import ROUNDED, TOP, Style, join_horizontal

PREVIEW_LIMIT = 256 * 1024  # bytes


class FileBrowser:
    def __init__(self, path: str = "."):
        self.picker = FilePicker(path=path, height=20)
        self.picker.file_allowed = False  # Enter only descends into directories
        self.preview = Viewport(width=52, height=20)
        self._refresh()

    def init(self):
        return None

    def _current(self):
        entries = self.picker.read_dir()
        if entries and self.picker.cursor < len(entries):
            return entries[self.picker.cursor]
        return None

    def _refresh(self):
        entry = self._current()
        if entry is None:
            self.preview.set_content("(empty directory)")
        elif entry.is_dir:
            try:
                names = sorted(os.listdir(entry.path))
            except OSError as exc:
                self.preview.set_content(f"(cannot list: {exc})")
                return
            listing = "\n".join("  " + n for n in names[:1000])
            self.preview.set_content(f"{entry.name}/\n\n{listing}")
        else:
            self.preview.set_content(self._read(entry.path))
        self.preview.goto_top()

    def _read(self, path: str) -> str:
        try:
            with open(path, "rb") as f:
                data = f.read(PREVIEW_LIMIT)
        except OSError as exc:
            return f"(cannot read: {exc})"
        if b"\x00" in data[:1024]:
            return "(binary file)"
        return data.decode("utf-8", "replace")

    def update(self, msg):
        if isinstance(msg, WindowSizeMsg):
            self.picker.height = max(3, msg.height - 4)
            self.preview.height = max(3, msg.height - 4)
            self.preview.width = max(20, msg.width - 42)
            self._refresh()
            return self, None
        if isinstance(msg, KeyMsg):
            if msg.key in ("q", "ctrl+c", "esc"):
                return self, quit
            if msg.key in ("pgup", "pgdown", "ctrl+u", "ctrl+d"):
                self.preview, _ = self.preview.update(msg)
                return self, None

        before = (self.picker.current_dir, self.picker.cursor)
        self.picker, _ = self.picker.update(msg)
        if (self.picker.current_dir, self.picker.cursor) != before:
            self._refresh()
        return self, None

    def view(self):
        t = get_theme()
        left = Style().border(ROUNDED).border_foreground(t.primary).padding(0, 1)
        right = Style().border(ROUNDED).border_foreground(t.faint).padding(0, 1)
        panes = join_horizontal(TOP, left.render(self.picker.view()), "  ", right.render(self.preview.view()))
        title = Style().bold().foreground(t.primary).render("File browser")
        hint = Style().foreground(t.muted).render(
            "↑/↓ move · enter open · backspace up · . hidden · PgUp/PgDn preview · q quit"
        )
        return f"{title}\n\n{panes}\n\n{hint}"


if __name__ == "__main__":
    from _shared import run_example

    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    run_example(FileBrowser(args[0] if args else "."))
