"""A persistent to-do list. Your tasks are saved to ~/.interrobang-todos.json,
so it's a real little daily tool, not just a demo.

    python examples/todo.py

a add a task · space (or enter) toggle done · d delete · ↑/↓ move · q quit.
"""

import json
import os

from interrobang import KeyMsg, get_theme, quit
from interrobang.components import TextInput
from interrobang.style import Style

STORE = os.path.expanduser("~/.interrobang-todos.json")


class Todo:
    def __init__(self, path: str = STORE):
        self.path = path
        self.items = self._load()
        self.cursor = 0
        self.adding = False
        self.input = TextInput()
        self.input.prompt = "new task › "
        self.input.blur()

    def init(self):
        return None

    # -- persistence -------------------------------------------------------

    def _load(self):
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            return []
        if not isinstance(data, list):
            return []
        return [
            {"text": str(d.get("text", "")), "done": bool(d.get("done"))}
            for d in data
            if isinstance(d, dict)
        ]

    def _save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.items, f, indent=2)
        except OSError:
            pass

    # -- update ------------------------------------------------------------

    def update(self, msg):
        if self.adding:
            return self._add_key(msg)
        if isinstance(msg, KeyMsg):
            key = msg.key
            if key in ("q", "ctrl+c"):
                return self, quit
            if key in ("up", "k"):
                self.cursor = max(0, self.cursor - 1)
            elif key in ("down", "j"):
                self.cursor = min(len(self.items) - 1, self.cursor + 1) if self.items else 0
            elif key == "a":
                self.adding = True
                self.input.reset()
                self.input.focus()
            elif key in ("enter", "space", "x"):
                self._toggle()
            elif key in ("d", "delete"):
                self._delete()
        return self, None

    def _toggle(self):
        if self.items:
            self.items[self.cursor]["done"] = not self.items[self.cursor]["done"]
            self._save()

    def _delete(self):
        if self.items:
            self.items.pop(self.cursor)
            self.cursor = min(self.cursor, len(self.items) - 1) if self.items else 0
            self._save()

    def _add_key(self, msg):
        if isinstance(msg, KeyMsg):
            if msg.key == "enter":
                text = self.input.value.strip()
                if text:
                    self.items.append({"text": text, "done": False})
                    self.cursor = len(self.items) - 1
                    self._save()
                self.adding = False
                self.input.blur()
                return self, None
            if msg.key == "esc":
                self.adding = False
                self.input.blur()
                return self, None
        self.input.update(msg)
        return self, None

    # -- view --------------------------------------------------------------

    def view(self):
        t = get_theme()
        title = (
            Style().bold().foreground(t.on_primary).background(t.primary).padding(0, 1)
            .render(" ‽ to-do ")
        )
        if self.adding:
            body = "add a task:\n\n  " + self.input.view()
        elif not self.items:
            body = Style().foreground(t.muted).render("nothing yet — press a to add a task")
        else:
            lines = []
            for i, item in enumerate(self.items):
                mark = "[x]" if item["done"] else "[ ]"
                text = item["text"]
                if item["done"]:
                    text = Style().faint().strikethrough().render(text)
                if i == self.cursor:
                    lines.append(Style().foreground(t.selection).bold().render(f"> {mark} ") + text)
                else:
                    lines.append(f"  {mark} {text}")
            body = "\n".join(lines)

        done = sum(1 for item in self.items if item["done"])
        status = Style().foreground(t.muted).render(f"{done}/{len(self.items)} done")
        hint = Style().foreground(t.muted).render("a add · space toggle · d delete · q quit")
        return f"{title}\n\n{body}\n\n{status}\n{hint}"


if __name__ == "__main__":
    from _shared import run_example

    run_example(Todo())
