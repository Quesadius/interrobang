"""Paginate a long list of items. Run: python examples/paginator.py.

Move pages with ←/→ (or h/l); q to quit.
"""

import interrobang as irb
from interrobang import KeyMsg, quit
from interrobang.components import Paginator
from interrobang.style import Color, Style

ITEMS = [f"Item #{i:02d}" for i in range(1, 48)]


class Model:
    def __init__(self):
        self.paginator = Paginator(per_page=8)
        self.paginator.set_total_items(len(ITEMS))

    def init(self):
        return None

    def update(self, msg):
        if isinstance(msg, KeyMsg) and msg.key in ("q", "ctrl+c", "esc"):
            return self, quit
        self.paginator, cmd = self.paginator.update(msg)
        return self, cmd

    def view(self):
        start, end = self.paginator.slice_bounds(len(ITEMS))
        item_style = Style().foreground(Color("#DDDDDD"))
        lines = [item_style.render("  " + item) for item in ITEMS[start:end]]
        title = Style().bold().foreground(Color("#7D56F4")).render("Paginated items")
        dots = Style().foreground(Color("#FF7CCB")).render(self.paginator.view())
        hint = Style().faint().render("←/→ change page · q quit")
        body = "\n".join(lines)
        return f"\n{title}\n\n{body}\n\n  {dots}\n\n  {hint}\n"


if __name__ == "__main__":
    from _shared import apply_theme_flag

    apply_theme_flag()
    irb.run(Model(), alt_screen=True)
