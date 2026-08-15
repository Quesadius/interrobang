"""A multi-field form: labelled inputs, Tab navigation, and validation.

    python examples/form.py

Tab / Shift-Tab (or ↑/↓) move between fields, type to edit, Enter submits when
everything is valid, Esc cancels. On submit it prints the collected values — a
handy skeleton for any "collect a few things from the user" script.
"""

from interrobang import KeyMsg, get_theme, quit
from interrobang.components import TextInput
from interrobang.style import ROUNDED, Style


class Field:
    def __init__(self, label, placeholder="", secret=False, validate=None):
        self.label = label
        self.validate = validate
        self.input = TextInput()
        self.input.prompt = ""
        self.input.placeholder = placeholder
        self.input.blur()
        if secret:
            from interrobang.components import EchoMode

            self.input.echo = EchoMode.PASSWORD

    @property
    def value(self):
        return self.input.value

    def error(self):
        return self.validate(self.value) if self.validate else None


def _required(v):
    return "required" if not v.strip() else None


def _email(v):
    if not v.strip():
        return "required"
    return None if "@" in v and "." in v.split("@")[-1] else "must look like name@host"


class Form:
    def __init__(self):
        self.fields = [
            Field("Name", "Ada Lovelace", validate=_required),
            Field("Email", "ada@example.com", validate=_email),
            Field("Password", "at least 8 chars", secret=True,
                  validate=lambda v: None if len(v) >= 8 else "at least 8 characters"),
        ]
        self.focus = 0
        self.fields[0].input.focus()
        self.submitted = None
        self.show_errors = False

    def init(self):
        return None

    def _move(self, delta):
        self.fields[self.focus].input.blur()
        self.focus = (self.focus + delta) % len(self.fields)
        self.fields[self.focus].input.focus()

    def _submit(self):
        self.show_errors = True
        if all(f.error() is None for f in self.fields):
            self.submitted = {f.label: f.value for f in self.fields}
            return self, quit
        # jump to the first invalid field
        for i, f in enumerate(self.fields):
            if f.error() is not None:
                self._move(i - self.focus)
                break
        return self, None

    def update(self, msg):
        if isinstance(msg, KeyMsg):
            if msg.key in ("ctrl+c", "esc"):
                return self, quit
            if msg.key in ("tab", "down"):
                self._move(1)
                return self, None
            if msg.key in ("shift+tab", "up"):
                self._move(-1)
                return self, None
            if msg.key == "enter":
                return self._submit()
        self.fields[self.focus].input.update(msg)
        return self, None

    def view(self):
        t = get_theme()
        rows = [Style().bold().foreground(t.primary).render("Sign up") + "\n"]
        for i, field in enumerate(self.fields):
            active = i == self.focus
            label = Style().foreground(t.primary if active else t.muted).render(f"{field.label:>9}: ")
            box = Style().border(ROUNDED).padding(0, 1).width(32)
            box = box.border_foreground(t.primary if active else t.faint)
            row = label + "\n" + box.render(field.input.view())
            err = field.error() if self.show_errors else None
            if err:
                row += "\n" + Style().foreground(t.selection).render(f"           {err}")
            rows.append(row)
        hint = Style().foreground(t.muted).render(
            "\ntab move · enter submit · esc cancel"
        )
        return "\n".join(rows) + hint


if __name__ == "__main__":
    from _shared import run_example

    final = run_example(Form())
    if final.submitted:
        print("Submitted:")
        for key, value in final.submitted.items():
            shown = "•" * len(value) if key == "Password" else value
            print(f"  {key}: {shown}")
