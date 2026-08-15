"""A key & mouse inspector: press anything and see exactly how interrobang
decodes it — the canonical name, key type, runes, and modifiers. Handy when
you're wiring up shortcuts and want to know what a key produces.

    python examples/keys.py

Press any key (mouse too — it's enabled). Ctrl+C quits.
"""

from interrobang import KeyMsg, MouseMsg, get_theme
from interrobang.style import Style


class KeyInspector:
    def __init__(self):
        self.events: list[tuple[str, str]] = []
        self.total = 0
        self.last = None

    def init(self):
        return None

    def update(self, msg):
        if isinstance(msg, KeyMsg):
            self.total += 1
            self.last = msg
            mods = "+".join(m for m, on in (("ctrl", msg.ctrl), ("alt", msg.alt), ("shift", msg.shift)) if on)
            detail = f"type={msg.type.name}  runes={msg.runes!r}  mods={mods or '-'}"
            self.events.insert(0, (msg.key, detail))
            self.events = self.events[:12]
        elif isinstance(msg, MouseMsg):
            self.total += 1
            self.last = msg
            name = f"{msg.action.name.lower()} {msg.button.name.lower()}"
            self.events.insert(0, (name, f"at ({msg.x}, {msg.y})"))
            self.events = self.events[:12]
        return self, None

    def view(self):
        t = get_theme()
        title = Style().bold().foreground(t.primary).render("Key inspector")

        if self.last is None:
            big = Style().foreground(t.muted).render("press any key…")
        elif isinstance(self.last, KeyMsg):
            big = Style().bold().foreground(t.on_primary).background(t.primary).padding(0, 2).render(self.last.key)
        else:
            label = f"{self.last.button.name.lower()} @ {self.last.x},{self.last.y}"
            big = Style().bold().foreground(t.on_selection).background(t.selection).padding(0, 2).render(label)

        rows = []
        for i, (name, detail) in enumerate(self.events):
            name_style = Style().foreground(t.selection if i == 0 else t.text).bold(i == 0)
            rows.append(name_style.render(f"{name:<18}") + Style().foreground(t.muted).render(detail))
        body = "\n".join(rows) if rows else Style().foreground(t.muted).render("(nothing yet)")

        hint = Style().foreground(t.muted).render(f"{self.total} events · ctrl+c to quit")
        return f"{title}\n\n  {big}\n\n{body}\n\n{hint}"


if __name__ == "__main__":
    from _shared import run_example

    run_example(KeyInspector(), mouse=True)
