"""A command-palette launcher: filter a list of commands and run the one you
pick. Run it, type to filter, pick with Enter, and the command runs in your
terminal after the UI closes.

    python examples/menu.py                 # built-in commands
    python examples/menu.py my-menu.json    # your own [{"label","cmd","desc"}]

Type to filter · ↑/↓ (or ctrl-p/ctrl-n) move · Enter run · Esc cancel.
"""

import json
import subprocess
import sys

from interrobang import KeyMsg, KeyType, WindowSizeMsg, get_theme, quit
from interrobang.style import Style

DEFAULT = [
    {"label": "Files", "cmd": "ls -la", "desc": "list this directory"},
    {"label": "Disk usage", "cmd": "df -h", "desc": "free space per mount"},
    {"label": "Date & time", "cmd": "date", "desc": "the current date and time"},
    {"label": "Uptime", "cmd": "uptime", "desc": "how long the machine's been up"},
    {"label": "Git status", "cmd": "git status -sb", "desc": "working tree status"},
    {"label": "Processes", "cmd": "ps aux | head -n 20", "desc": "the top process rows"},
]


class Menu:
    def __init__(self, entries=None):
        self.entries = entries if entries is not None else DEFAULT
        self.query = ""
        self.cursor = 0
        self.height = 12
        self.command = None

    def init(self):
        return None

    def matches(self):
        q = self.query.lower()
        return [e for e in self.entries if q in e["label"].lower() or q in e.get("desc", "").lower()]

    def update(self, msg):
        if isinstance(msg, WindowSizeMsg):
            self.height = max(3, msg.height - 2)
            return self, None
        if not isinstance(msg, KeyMsg):
            return self, None

        key = msg.key
        if key in ("ctrl+c", "esc"):
            return self, quit
        if key == "enter":
            items = self.matches()
            if items:
                self.command = items[min(self.cursor, len(items) - 1)]["cmd"]
            return self, quit
        if key in ("up", "ctrl+p"):
            self.cursor = max(0, self.cursor - 1)
        elif key in ("down", "ctrl+n"):
            self.cursor = min(max(0, len(self.matches()) - 1), self.cursor + 1)
        elif key == "backspace":
            self.query, self.cursor = self.query[:-1], 0
        elif key == "ctrl+u":
            self.query, self.cursor = "", 0
        elif msg.type is KeyType.SPACE:
            self.query, self.cursor = self.query + " ", 0
        elif msg.type is KeyType.RUNES and not msg.ctrl and not msg.alt:
            self.query, self.cursor = self.query + msg.runes, 0
        return self, None

    def view(self):
        t = get_theme()
        items = self.matches()
        self.cursor = max(0, min(self.cursor, len(items) - 1)) if items else 0
        start = max(0, self.cursor - self.height + 1)
        window = items[start : start + self.height]

        prompt = Style().foreground(t.primary).bold().render("run › ")
        rows = [prompt + self.query]
        for i, entry in enumerate(window):
            active = start + i == self.cursor
            label = entry["label"]
            desc = entry.get("desc", "")
            if active:
                line = Style().foreground(t.selection).bold().render(f"› {label}")
            else:
                line = Style().foreground(t.text).render(f"  {label}")
            if desc:
                line += Style().foreground(t.muted).render(f"  — {desc}")
            rows.append(line)
        if not items:
            rows.append(Style().foreground(t.muted).render("  (no matches)"))

        chosen = items[self.cursor]["cmd"] if items else ""
        footer = Style().faint().render(f"$ {chosen}") if chosen else ""
        return "\n".join(rows) + ("\n\n" + footer if footer else "")


def _load_entries():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not args:
        return None
    with open(args[0], encoding="utf-8") as f:
        data = json.load(f)
    return [e for e in data if "label" in e and "cmd" in e]


if __name__ == "__main__":
    from _shared import run_example

    final = run_example(Menu(_load_entries()))
    if final.command:
        # The UI has closed and the terminal is restored, so run in the foreground.
        raise SystemExit(subprocess.call(final.command, shell=True))
