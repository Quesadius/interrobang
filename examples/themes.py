"""Switching themes. Run: python examples/themes.py.

Prints the same little panel under each built-in theme so you can compare them.
Switching the whole app's look is a single call: ``irb.set_theme(theme)`` before
you build your components.
"""

from interrobang import CHARM, SOLARIZED_DARK, get_theme, set_theme
from interrobang.components import DOTS, Item, List, Progress, Spinner
from interrobang.style import ROUNDED, Style, join_vertical


def panel():
    t = get_theme()
    title = (
        Style().bold().foreground(t.on_primary).background(t.primary).padding(0, 1)
        .render(f" {t.name} ")
    )
    spinner = Spinner(DOTS)
    spinner.frame = 2
    bar = Progress(width=24)
    items = List([Item("Exclaim"), Item("Question"), Item("Interrobang")], width=24, height=8)
    items.show_description = False
    items.show_status_bar = False
    items.cursor = 1
    body = join_vertical(
        0.0,
        f"{spinner.view()} loading...",
        "",
        bar.view_as(0.6),
        "",
        items.view(),
    )
    return Style().border(ROUNDED).border_foreground(t.secondary).padding(1, 2).render(
        title + "\n\n" + body
    )


def main():
    for theme in (SOLARIZED_DARK, CHARM):
        set_theme(theme)
        print()
        print(panel())
    print()


if __name__ == "__main__":
    main()
