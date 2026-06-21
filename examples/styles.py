"""A gallery of the styling engine. Prints to stdout -- no TTY required.

Run it::

    python examples/styles.py
"""

from interrobang.style import (
    DOUBLE,
    ROUNDED,
    THICK,
    AdaptiveColor,
    Color,
    Style,
)


def main():
    print()
    print(Style().bold().underline().foreground(Color("#7D56F4")).render("interrobang styling gallery"))
    print()

    # Text attributes.
    attrs = [
        Style().bold().render("bold"),
        Style().faint().render("faint"),
        Style().italic().render("italic"),
        Style().underline().render("underline"),
        Style().strikethrough().render("strikethrough"),
        Style().reverse().render("reverse"),
    ]
    print("  " + "   ".join(attrs))
    print()

    # Foreground colors across the spectrum.
    swatches = [Style().foreground(Color(f"#{r:02x}50a0")).render("██") for r in range(0, 256, 32)]
    print("  foreground: " + "".join(swatches))

    # A filled badge.
    badge = (
        Style()
        .bold()
        .foreground(Color("#FAFAFA"))
        .background(Color("#FF5F87"))
        .padding(0, 2)
    )
    print("  badge:      " + badge.render("NEW"))
    print()

    # Borders.
    for name, border in (("rounded", ROUNDED), ("thick", THICK), ("double", DOUBLE)):
        box = Style().border(border).border_foreground(Color("#7D56F4")).padding(0, 1)
        print(_indent(box.render(name)))
        print()

    # Adaptive color note.
    adaptive = Style().foreground(AdaptiveColor(light="#0000AA", dark="#88CCFF"))
    print("  " + adaptive.render("this color adapts to your terminal background"))

    # A composed card.
    card = (
        Style()
        .border(ROUNDED)
        .border_foreground(Color("63"))
        .padding(1, 2)
        .width(34)
    )
    title = Style().bold().foreground(Color("#FF7CCB"))
    body = Style().foreground(Color("#DDDDDD"))
    content = title.render("interrobang ‽") + "\n\n" + body.render(
        "A pure-Python toolkit for building delightful terminal UIs."
    )
    print()
    print(_indent(card.render(content)))
    print()


def _indent(block, n=2):
    pad = " " * n
    return "\n".join(pad + line for line in block.split("\n"))


if __name__ == "__main__":
    main()
