"""Composing rendered blocks with the layout helpers. Prints to stdout.

Run it::

    python examples/layout.py
"""

from interrobang.style import (
    CENTER,
    ROUNDED,
    TOP,
    Color,
    Style,
    join_horizontal,
    join_vertical,
    place,
)


def card(title, body, color):
    title_style = Style().bold().foreground(Color("#FAFAFA")).background(Color(color)).padding(0, 1)
    frame = Style().border(ROUNDED).border_foreground(Color(color)).padding(1, 2).width(20)
    return frame.render(title_style.render(title) + "\n\n" + body)


def main():
    print()
    print(Style().bold().foreground(Color("#7D56F4")).render("Horizontal join (top-aligned):"))
    a = card("Red", "A short body.", "#FF5F87")
    b = card("Blue", "A slightly longer body that wraps.", "#5F87FF")
    c = card("Green", "Mid.", "#5FD787")
    print(join_horizontal(TOP, a, "  ", b, "  ", c))
    print()

    print(Style().bold().foreground(Color("#7D56F4")).render("Vertical join (centered):"))
    print(join_vertical(CENTER, "small", "a much wider line here", "mid-size"))
    print()

    print(Style().bold().foreground(Color("#7D56F4")).render("Place in a 50x7 box (centered):"))
    badge = Style().bold().foreground(Color("#FAFAFA")).background(Color("#7D56F4")).padding(1, 3).render("‽")
    boxed = place(50, 7, CENTER, CENTER, badge)
    framed = Style().border(ROUNDED).border_foreground(Color("240"))
    print(framed.render(boxed))
    print()


if __name__ == "__main__":
    main()
