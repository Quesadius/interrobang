"""A selectable, filterable list. Run: python examples/list.py.

Move with ↑/↓ (or j/k), filter with /, select with enter, q to quit.
"""

import interrobang as irb
from interrobang import KeyMsg, quit
from interrobang.components import Item, List
from interrobang.style import Color, Style

SNACKS = [
    Item("Pocky", "Biscuit sticks dipped in chocolate"),
    Item("Ramen", "Wheat noodles in savory broth"),
    Item("Mochi", "Chewy rice cake, often filled"),
    Item("Taiyaki", "Fish-shaped cake with sweet filling"),
    Item("Dango", "Skewered rice dumplings"),
    Item("Senbei", "Crunchy rice crackers"),
    Item("Matcha KitKat", "Green tea chocolate wafer"),
    Item("Onigiri", "Rice ball wrapped in nori"),
    Item("Dorayaki", "Pancakes with red bean paste"),
    Item("Melonpan", "Sweet bun with a crisp crust"),
]


class Model:
    def __init__(self):
        self.list = List(SNACKS, width=44, height=16)
        self.list.title = "Snacks"
        self.chosen = None

    def init(self):
        return None

    def update(self, msg):
        if isinstance(msg, KeyMsg):
            if msg.key in ("ctrl+c", "q") and not self.list.filtering:
                return self, quit
            if msg.key == "enter" and not self.list.filtering:
                item = self.list.selected_item()
                if item:
                    self.chosen = item.title
                    return self, quit
        self.list, cmd = self.list.update(msg)
        return self, cmd

    def view(self):
        hint = Style().faint().render("↑/↓ move · / filter · enter select · q quit")
        return self.list.view() + "\n\n" + hint


if __name__ == "__main__":
    from _shared import apply_theme_flag

    apply_theme_flag()
    final = irb.run(Model(), alt_screen=True)
    if final.chosen:
        print(f"You chose: {final.chosen}")
