"""A text input prompt. Run: python examples/textinput.py (enter to submit)."""

import interrobang as irb
from interrobang import KeyMsg, quit
from interrobang.components import TextInput
from interrobang.style import Color, Style


class Model:
    def __init__(self):
        self.input = TextInput()
        self.input.placeholder = "your name"
        self.input.prompt = "name › "
        self.input.prompt_style = Style().foreground(Color("#7D56F4")).bold()
        self.submitted = None

    def init(self):
        return None

    def update(self, msg):
        if isinstance(msg, KeyMsg):
            if msg.key in ("ctrl+c", "esc"):
                return self, quit
            if msg.key == "enter":
                self.submitted = self.input.value
                return self, quit
        self.input, cmd = self.input.update(msg)
        return self, cmd

    def view(self):
        title = Style().bold().foreground(Color("#FF7CCB")).render("What's your name?")
        hint = Style().faint().render("enter submit · esc cancel")
        return f"\n  {title}\n\n  {self.input.view()}\n\n  {hint}\n"


if __name__ == "__main__":
    final = irb.run(Model(), alt_screen=True)
    if final.submitted:
        print(f"Hello, {final.submitted}!")
