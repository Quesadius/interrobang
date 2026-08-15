"""An interactive line picker for shell pipelines, like a tiny ``fzf``.

Reads candidate lines from stdin (or a file argument), lets you filter them by
typing and pick one with the arrow keys, and prints your choice to stdout —
so it composes:

    git branch | python examples/pick.py | xargs git switch
    ls | python examples/pick.py

Type to filter, ↑/↓ (or ctrl-p/ctrl-n) to move, Enter to select, Esc to cancel.
"""

import sys

from interrobang import KeyMsg, KeyType, WindowSizeMsg, get_theme, quit
from interrobang.style import Style

SAMPLE = ["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "golf", "hotel"]


class Picker:
    def __init__(self, choices: list[str] | None = None, prompt: str = "› "):
        self.choices = choices if choices is not None else list(SAMPLE)
        self.prompt = prompt
        self.query = ""
        self.cursor = 0
        self.height = 12
        self.selected: str | None = None

    def init(self):
        return None

    def matches(self) -> list[str]:
        needle = self.query.lower()
        return [c for c in self.choices if needle in c.lower()]

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
                self.selected = items[min(self.cursor, len(items) - 1)]
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

        # Scroll a window of results around the cursor.
        start = max(0, self.cursor - self.height + 1)
        window = items[start : start + self.height]

        prompt = Style().foreground(t.primary).bold().render(self.prompt)
        count = Style().foreground(t.muted).render(f"  {len(items)}/{len(self.choices)}")
        rows = [prompt + self.query + count]
        for i, item in enumerate(window):
            if start + i == self.cursor:
                rows.append(Style().foreground(t.selection).bold().render("› " + item))
            else:
                rows.append(Style().foreground(t.text).render("  " + item))
        if not items:
            rows.append(Style().foreground(t.muted).render("  (no matches)"))
        return "\n".join(rows)


def _read_choices() -> list[str] | None:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if args:
        with open(args[0], encoding="utf-8", errors="replace") as f:
            return [line.rstrip("\n") for line in f if line.strip()]
    if not sys.stdin.isatty():
        return [line.rstrip("\n") for line in sys.stdin if line.strip()]
    return None


if __name__ == "__main__":
    from _shared import run_example

    choices = _read_choices()
    if choices is not None and not choices:
        sys.exit("pick: no input lines")
    final = run_example(Picker(choices), tty=True)
    if final.selected is not None:
        print(final.selected)
    else:
        sys.exit(1)  # nothing picked
