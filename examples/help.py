"""Declarative key bindings and a help view. Run: python examples/help.py.

Press ? to toggle full help, the bound keys to act, q to quit.
"""

import interrobang as irb
from interrobang import KeyMsg, quit
from interrobang.components import Help, KeyBinding
from interrobang.style import Color, Style


class Keys:
    up = KeyBinding(["up", "k"], "↑/k", "move up")
    down = KeyBinding(["down", "j"], "↓/j", "move down")
    left = KeyBinding(["left", "h"], "←/h", "move left")
    right = KeyBinding(["right", "l"], "→/l", "move right")
    toggle = KeyBinding(["?"], "?", "toggle help")
    quit = KeyBinding(["q", "ctrl+c"], "q", "quit")


class Model:
    def __init__(self):
        self.help = Help()
        self.last = "(nothing yet)"

    def init(self):
        return None

    def update(self, msg):
        if Keys.quit.matches(msg):
            return self, quit
        if Keys.toggle.matches(msg):
            self.help.show_all = not self.help.show_all
        for binding in (Keys.up, Keys.down, Keys.left, Keys.right):
            if binding.matches(msg):
                self.last = binding.help_desc
        return self, None

    def view(self):
        title = Style().bold().foreground(Color("#7D56F4")).render("Help component demo")
        last = Style().foreground(Color("#FF7CCB")).render(f"last action: {self.last}")
        bindings = [Keys.up, Keys.down, Keys.left, Keys.right, Keys.toggle, Keys.quit]
        if self.help.show_all:
            help_view = self.help.full_view(
                [[Keys.up, Keys.down], [Keys.left, Keys.right], [Keys.toggle, Keys.quit]]
            )
        else:
            help_view = self.help.short_view(bindings)
        return f"\n  {title}\n\n  {last}\n\n  {help_view}\n"


if __name__ == "__main__":
    irb.run(Model(), alt_screen=True)
