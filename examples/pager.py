"""A file / stdin pager, like a tiny ``less``.

    python examples/pager.py README.md
    git log | python examples/pager.py

Scroll with ↑/↓/PgUp/PgDn/Home/End (or j/k/g/G), search with ``/`` then Enter,
jump to the next match with ``n``, and quit with ``q``. Long lines are wrapped
to the window width. A genuinely useful ~90 lines you can lift into any script.
"""

import sys

from interrobang import KeyMsg, KeyType, WindowSizeMsg, get_theme, quit, wrap
from interrobang.components import Viewport
from interrobang.style import Style

DEFAULT_TEXT = """\
interrobang pager ‽

No file was given, so this is the built-in help.

Usage:
    python examples/pager.py <file>
    <some command> | python examples/pager.py

Keys:
    ↑ / k        up one line
    ↓ / j        down one line
    PgUp / PgDn  page up / down
    g / G        top / bottom
    /            search, then Enter
    n            next match
    q            quit
""" * 3


class Pager:
    def __init__(self, text: str | None = None, title: str = "pager"):
        self.raw = text if text is not None else DEFAULT_TEXT
        self.title = title
        self.viewport = Viewport(width=80, height=20)
        self.lines: list[str] = []
        self.searching = False
        self.query = ""
        self.status = ""
        self._reflow()

    def init(self):
        return None

    def _reflow(self):
        self.lines = wrap(self.raw, max(1, self.viewport.width)).split("\n")
        self.viewport.set_content("\n".join(self.lines))

    def _goto(self, line: int):
        max_offset = max(0, self.viewport.total_lines - self.viewport.height)
        self.viewport.y_offset = max(0, min(line, max_offset))

    def _find_next(self, from_top: bool = False):
        if not self.query:
            return
        needle = self.query.lower()
        start = 0 if from_top else self.viewport.y_offset + 1
        order = list(range(start, len(self.lines))) + list(range(0, start))
        for i in order:
            if needle in self.lines[i].lower():
                self._goto(i)
                self.status = f"/{self.query}"
                return
        self.status = f"/{self.query} — not found"

    def update(self, msg):
        if isinstance(msg, WindowSizeMsg):
            self.viewport.width = max(20, msg.width)
            self.viewport.height = max(3, msg.height - 2)
            self._reflow()
            return self, None

        if isinstance(msg, KeyMsg):
            if self.searching:
                return self._search_key(msg)
            if msg.key in ("q", "ctrl+c", "esc"):
                return self, quit
            if msg.key == "/":
                self.searching, self.query, self.status = True, "", ""
                return self, None
            if msg.key == "n":
                self._find_next()
                return self, None

        self.viewport, _ = self.viewport.update(msg)
        return self, None

    def _search_key(self, msg):
        if msg.key == "enter":
            self.searching = False
            self._find_next(from_top=True)
        elif msg.key == "esc":
            self.searching, self.query = False, ""
        elif msg.key == "backspace":
            self.query = self.query[:-1]
        elif msg.type is KeyType.SPACE:
            self.query += " "
        elif msg.type is KeyType.RUNES and not msg.ctrl and not msg.alt:
            self.query += msg.runes
        return self, None

    def view(self):
        t = get_theme()
        header = (
            Style().bold().foreground(t.on_primary).background(t.primary)
            .width(self.viewport.width).render(f" {self.title}")
        )
        if self.searching:
            footer = Style().foreground(t.primary).render(f"/{self.query}")
        else:
            pct = int(self.viewport.scroll_percent() * 100)
            note = self.status or "/ search · n next · q quit"
            footer = Style().foreground(t.muted).render(f"{pct:>3}%  ·  {note}")
        return f"{header}\n{self.viewport.view()}\n{footer}"


if __name__ == "__main__":
    from _shared import run_example

    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if args:
        with open(args[0], encoding="utf-8", errors="replace") as f:
            run_example(Pager(f.read(), title=args[0]), tty=True)
    elif not sys.stdin.isatty():
        run_example(Pager(sys.stdin.read(), title="stdin"), tty=True)
    else:
        run_example(Pager(), tty=True)
