"""A follow-mode log tailer, like ``tail -f`` with a live filter.

    python examples/logtail.py /var/log/system.log
    python examples/logtail.py            # a self-generating demo log

Follows the file as it grows and sticks to the bottom. Press ``/`` to filter to
matching lines, ``f`` to toggle follow, ``g``/``G`` for top/bottom, arrows/PgUp/
PgDn to scroll (which pauses follow), and ``q`` to quit.
"""

import os
import sys
import time
from dataclasses import dataclass

from interrobang import KeyMsg, KeyType, WindowSizeMsg, get_theme, quit
from interrobang.components import Viewport
from interrobang.style import Style

POLL_INTERVAL = 0.5
GEN_INTERVAL = 0.9
MAX_LINES = 5000


@dataclass(frozen=True)
class Chunk:
    lines: tuple
    offset: int


@dataclass(frozen=True)
class GenLine:
    pass


class Tail:
    def __init__(self, path: str | None = None):
        self.path = path
        self.offset = 0
        self.raw: list[str] = []
        self.viewport = Viewport(width=80, height=20)
        self.follow = True
        self.filtering = False
        self.query = ""
        self.gen_n = 0
        if path is None:  # demo mode: seed a few lines
            self.raw = [f"{time.strftime('%H:%M:%S')}  seeded line {i}" for i in range(1, 6)]
            self._reflow()

    def init(self):
        return self._poll() if self.path else self._gen()

    # -- background readers ------------------------------------------------

    def _poll(self):
        path, offset = self.path, self.offset

        def cmd():
            time.sleep(POLL_INTERVAL)
            try:
                start = 0 if os.path.getsize(path) < offset else offset
                with open(path, "rb") as f:
                    f.seek(start)
                    data = f.read()
            except OSError:
                return Chunk((), offset)
            nl = data.rfind(b"\n")
            if nl == -1:
                return Chunk((), start)
            consumed = data[: nl + 1]
            lines = consumed.decode("utf-8", "replace").split("\n")[:-1]
            return Chunk(tuple(lines), start + len(consumed))

        return cmd

    def _gen(self):
        def cmd():
            time.sleep(GEN_INTERVAL)
            return GenLine()

        return cmd

    # -- helpers -----------------------------------------------------------

    def _visible(self):
        if not self.query:
            return self.raw
        needle = self.query.lower()
        return [line for line in self.raw if needle in line.lower()]

    def _reflow(self):
        self.viewport.set_content("\n".join(self._visible()))
        if self.follow:
            self.viewport.goto_bottom()

    def _append(self, lines):
        self.raw.extend(lines)
        if len(self.raw) > MAX_LINES:
            self.raw = self.raw[-MAX_LINES:]
        self._reflow()

    # -- update ------------------------------------------------------------

    def update(self, msg):
        if isinstance(msg, WindowSizeMsg):
            self.viewport.width = max(20, msg.width)
            self.viewport.height = max(3, msg.height - 2)
            self._reflow()
            return self, None
        if isinstance(msg, Chunk):
            if msg.lines:
                self._append(msg.lines)
            self.offset = msg.offset
            return self, (self._poll() if self.path else None)
        if isinstance(msg, GenLine):
            self.gen_n += 1
            self._append([f"{time.strftime('%H:%M:%S')}  demo event #{self.gen_n}"])
            return self, self._gen()
        if isinstance(msg, KeyMsg):
            return self._key(msg)
        return self, None

    def _key(self, msg):
        if self.filtering:
            return self._filter_key(msg)
        key = msg.key
        if key in ("q", "ctrl+c"):
            return self, quit
        if key == "/":
            self.filtering, self.query = True, ""
            return self, None
        if key == "f":
            self.follow = not self.follow
            if self.follow:
                self.viewport.goto_bottom()
            return self, None
        if key in ("G", "end"):
            self.follow = True
            self.viewport.goto_bottom()
            return self, None
        if key in ("g", "home"):
            self.follow = False
            self.viewport.goto_top()
            return self, None
        if key in ("up", "k", "pgup", "b", "ctrl+u"):
            self.follow = False
        self.viewport, _ = self.viewport.update(msg)
        return self, None

    def _filter_key(self, msg):
        if msg.key in ("enter", "esc"):
            if msg.key == "esc":
                self.query = ""
            self.filtering = False
        elif msg.key == "backspace":
            self.query = self.query[:-1]
        elif msg.type is KeyType.SPACE:
            self.query += " "
        elif msg.type is KeyType.RUNES and not msg.ctrl and not msg.alt:
            self.query += msg.runes
        self._reflow()
        return self, None

    # -- view --------------------------------------------------------------

    def view(self):
        t = get_theme()
        src = self.path or "demo log"
        flag = "FOLLOW" if self.follow else "PAUSED"
        header = (
            Style().bold().foreground(t.on_primary).background(t.primary)
            .width(self.viewport.width).render(f" {src}  [{flag}]")
        )
        if self.filtering:
            footer = Style().foreground(t.primary).render(f"/{self.query}")
        else:
            shown, total = len(self._visible()), len(self.raw)
            note = f"{shown}/{total} lines"
            if self.query:
                note += f"  ·  filter: {self.query}"
            footer = Style().foreground(t.muted).render(f"{note}  ·  f follow · / filter · q quit")
        return f"{header}\n{self.viewport.view()}\n{footer}"


if __name__ == "__main__":
    from _shared import run_example

    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    run_example(Tail(args[0] if args else None))
