"""A collapsible, syntax-highlighted JSON viewer.

    python examples/jsonview.py package.json
    curl -s https://api.github.com/repos/python/cpython | python examples/jsonview.py

↑/↓ (or j/k) move · Enter/Space or ←/→ collapse/expand · ← also jumps to the
parent · g/G top/bottom · q quits. Handy for spelunking API responses.
"""

import json
import sys

from interrobang import KeyMsg, KeyType, WindowSizeMsg, get_theme, quit, truncate
from interrobang.style import Style

SAMPLE = {
    "name": "interrobang",
    "version": "0.1.0",
    "punctuation": True,
    "stars": 1,
    "themes": ["solarized-dark", "solarized-light", "neon"],
    "author": {"handle": "you", "verified": False, "links": None},
    "marks": [
        {"glyph": "‽", "name": "interrobang"},
        {"glyph": "?", "name": "question mark"},
    ],
}


class JSONView:
    def __init__(self, data=None, title="json"):
        self.data = SAMPLE if data is None else data
        self.title = title
        self.collapsed: set[tuple] = set()
        self.cursor = 0
        self.offset = 0
        self.width = 80
        self.height = 20
        self.rows: list[dict] = []
        self._rebuild()

    def init(self):
        return None

    # -- flatten the tree into visible rows --------------------------------

    def _rebuild(self):
        self.rows = []
        self._walk(self.data, (), None)
        self.cursor = max(0, min(self.cursor, len(self.rows) - 1))
        self._clamp_offset()

    def _walk(self, node, path, key):
        container = isinstance(node, (dict, list))
        self.rows.append({"path": path, "depth": len(path), "key": key,
                          "node": node, "container": container})
        if container and path not in self.collapsed:
            items = node.items() if isinstance(node, dict) else enumerate(node)
            for k, v in items:
                self._walk(v, path + (k,), k)

    def _clamp_offset(self):
        if self.cursor < self.offset:
            self.offset = self.cursor
        elif self.cursor >= self.offset + self.height:
            self.offset = self.cursor - self.height + 1

    # -- update ------------------------------------------------------------

    def update(self, msg):
        if isinstance(msg, WindowSizeMsg):
            self.width = max(20, msg.width)
            self.height = max(3, msg.height - 2)
            self._clamp_offset()
            return self, None
        if not isinstance(msg, KeyMsg):
            return self, None

        key = msg.key
        if key in ("q", "ctrl+c", "esc"):
            return self, quit
        if key in ("up", "k"):
            self.cursor = max(0, self.cursor - 1)
        elif key in ("down", "j"):
            self.cursor = min(len(self.rows) - 1, self.cursor + 1)
        elif key in ("home", "g"):
            self.cursor = 0
        elif key in ("end", "G"):
            self.cursor = len(self.rows) - 1
        elif key in ("enter", "space"):
            self._toggle()
        elif key == "right":
            self._expand()
        elif key == "left":
            self._collapse_or_parent()
        self._clamp_offset()
        return self, None

    def _row(self):
        return self.rows[self.cursor] if self.rows else None

    def _toggle(self):
        row = self._row()
        if row and row["container"]:
            path = row["path"]
            self.collapsed.symmetric_difference_update({path})
            self._rebuild()

    def _expand(self):
        row = self._row()
        if row and row["container"] and row["path"] in self.collapsed:
            self.collapsed.discard(row["path"])
            self._rebuild()

    def _collapse_or_parent(self):
        row = self._row()
        if not row:
            return
        if row["container"] and row["path"] not in self.collapsed:
            self.collapsed.add(row["path"])
            self._rebuild()
        elif row["path"]:
            parent = row["path"][:-1]
            for i, r in enumerate(self.rows):
                if r["path"] == parent:
                    self.cursor = i
                    break

    # -- view --------------------------------------------------------------

    def _scalar(self, node):
        t = get_theme()
        if node is None:
            return Style().foreground(t.selection).render("null")
        if isinstance(node, bool):
            return Style().foreground(t.selection).render("true" if node else "false")
        if isinstance(node, (int, float)):
            return Style().foreground(t.secondary).render(json.dumps(node))
        return Style().foreground(t.gradient_end).render(json.dumps(node))

    def _render(self, row, selected):
        t = get_theme()
        indent = "  " * row["depth"]
        key = row["key"]
        if key is None:
            keystr = ""
        elif isinstance(key, int):
            keystr = Style().foreground(t.muted).render(f"{key}: ")
        else:
            keystr = Style().foreground(t.primary).render(json.dumps(key)) + Style().foreground(t.muted).render(": ")

        if row["container"]:
            node = row["node"]
            collapsed = row["path"] in self.collapsed
            glyph = Style().foreground(t.muted).render("▸ " if collapsed else "▾ ")
            if isinstance(node, dict):
                brace, n, unit = "{…}" if collapsed else "{", len(node), "keys"
            else:
                brace, n, unit = "[…]" if collapsed else "[", len(node), "items"
            value = glyph + Style().foreground(t.secondary).render(brace)
            if collapsed:
                value += Style().foreground(t.muted).render(f" {n} {unit}")
        else:
            value = self._scalar(row["node"])

        prefix = Style().foreground(t.selection).bold().render("▌ ") if selected else "  "
        return truncate(prefix + indent + keystr + value, self.width)

    def view(self):
        t = get_theme()
        header = (
            Style().bold().foreground(t.on_primary).background(t.primary)
            .width(self.width).render(f" {self.title}")
        )
        window = self.rows[self.offset : self.offset + self.height]
        body = "\n".join(self._render(r, self.offset + i == self.cursor) for i, r in enumerate(window))
        pos = f"{self.cursor + 1}/{len(self.rows)}"
        footer = Style().foreground(t.muted).render(
            f"{pos}  ·  enter/←/→ fold · g/G ends · q quit"
        )
        return f"{header}\n{body}\n{footer}"


if __name__ == "__main__":
    from _shared import run_example

    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    raw = None
    title = "json"
    if args:
        with open(args[0], encoding="utf-8") as f:
            raw, title = f.read(), args[0]
    elif not sys.stdin.isatty():
        raw, title = sys.stdin.read(), "stdin"

    data = None
    if raw is not None:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            sys.exit(f"jsonview: invalid JSON: {exc}")

    run_example(JSONView(data, title), tty=True)
