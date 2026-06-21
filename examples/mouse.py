"""Mouse reporting. Run: python examples/mouse.py and click/scroll. q to quit."""

import interrobang as irb
from interrobang import KeyMsg, MouseMsg, quit
from interrobang.style import Color, Style


class Model:
    def __init__(self):
        self.last = "move, click, or scroll the mouse"

    def init(self):
        return None

    def update(self, msg):
        if isinstance(msg, KeyMsg) and msg.key in ("q", "ctrl+c", "esc"):
            return self, quit
        if isinstance(msg, MouseMsg):
            self.last = (
                f"{msg.action.name.lower()} {msg.button.name.lower()} "
                f"at ({msg.x}, {msg.y})"
            )
        return self, None

    def view(self):
        title = Style().bold().foreground(Color("#7D56F4")).render("Mouse demo")
        event = Style().foreground(Color("#FF7CCB")).render(self.last)
        hint = Style().faint().render("q quit")
        return f"\n  {title}\n\n  {event}\n\n  {hint}\n"


if __name__ == "__main__":
    irb.run(Model(), alt_screen=True, mouse=True)
