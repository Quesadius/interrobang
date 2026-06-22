"""Generate the documentation screenshots in docs/images/.

Each image is produced from the *real* output of interrobang's styling engine
and components, then rendered to an SVG terminal window by ``tools/termshot``.
Run it from anywhere with the project's environment:

    python tools/generate_images.py

Regenerate after changing component visuals so the docs stay accurate.
"""

from __future__ import annotations

import os
import sys

# Make sure interrobang and this package are importable when run directly.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from termshot import render_animated_svg, render_svg  # noqa: E402

from interrobang import KeyMsg, KeyType  # noqa: E402
from interrobang.components import (  # noqa: E402
    DOTS,
    Column,
    FilePicker,
    Help,
    Item,
    KeyBinding,
    List,
    Paginator,
    Progress,
    Spinner,
    Table,
    TextInput,
    Viewport,
)
from interrobang.style import (  # noqa: E402
    DOUBLE,
    ROUNDED,
    THICK,
    TOP,
    Color,
    Profile,
    Style,
    join_horizontal,
    join_vertical,
    set_color_profile,
    set_has_dark_background,
)

set_color_profile(Profile.TRUECOLOR)
set_has_dark_background(True)

IMAGES_DIR = os.path.join(ROOT, "docs", "images")

SNACKS = [
    Item("Pocky", "Biscuit sticks dipped in chocolate"),
    Item("Ramen", "Wheat noodles in savory broth"),
    Item("Mochi", "Chewy rice cake, often filled"),
    Item("Taiyaki", "Fish-shaped cake with sweet filling"),
    Item("Dango", "Skewered rice dumplings"),
    Item("Senbei", "Crunchy rice crackers"),
]

TABLE_ROWS = [
    ["bubbletea", "Go", "Charm", "29k"],
    ["lipgloss", "Go", "Charm", "9k"],
    ["rich", "Python", "Textualize", "49k"],
    ["textual", "Python", "Textualize", "27k"],
    ["interrobang", "Python", "you", "1"],
    ["ratatui", "Rust", "ratatui-org", "11k"],
]


# --- subjects -----------------------------------------------------------------


def hero() -> str:
    sp = Spinner(DOTS, Style().foreground(Color("#FF7CCB")))
    sp.frame = 2
    bar = Progress(width=30).with_gradient("#FF7CCB", "#FDFF8C")
    lst = List(
        [Item(t) for t in ("Fetch deps", "Compile", "Run tests", "Build", "Package", "Publish")],
        width=26,
        height=10,
    )
    lst.title = "Pipeline"
    lst.show_description = False
    lst.show_status_bar = False
    lst.cursor = 2

    header = (
        Style().bold().foreground(Color("#FAFAFA")).background(Color("#7D56F4")).padding(0, 2)
        .render("interrobang dashboard ‽")
    )
    status_panel = Style().border(ROUNDED).border_foreground(Color("63")).padding(1, 2).width(34)
    status_body = join_vertical(
        0.0, f"{sp.view()} working...", "", "Build progress:", bar.view_as(0.6)
    )
    list_panel = Style().border(ROUNDED).border_foreground(Color("240")).padding(1, 2)
    panels = join_horizontal(TOP, status_panel.render(status_body), "  ", list_panel.render(lst.view()))
    footer = Style().faint().render("↑/↓ move the list · q quit")
    return "\n".join([header, "", panels, "", footer])


def counter() -> str:
    title = Style().bold().foreground(Color("#7D56F4")).render("interrobang counter")
    number = (
        Style().bold().foreground(Color("#FAFAFA")).background(Color("#7D56F4")).padding(0, 2)
        .render("42")
    )
    hint = Style().faint().render("↑/↓ change · q quit")
    return "\n".join([title, "", "  " + number, "", hint])


def styling() -> str:
    title = Style().bold().foreground(Color("#7D56F4")).render("Styling gallery")
    attrs = "   ".join(
        [
            Style().bold().render("bold"),
            Style().italic().render("italic"),
            Style().underline().render("underline"),
            Style().strikethrough().render("strike"),
            Style().reverse().render(" reverse "),
        ]
    )
    badge = (
        Style().bold().foreground(Color("#FAFAFA")).background(Color("#FF5F87")).padding(0, 2)
        .render("NEW")
    )
    swatch = "".join(Style().foreground(Color(f"#{v:02x}7df4")).render("█") for v in range(0, 256, 12))
    boxes = join_horizontal(
        TOP,
        Style().border(ROUNDED).border_foreground(Color("#7D56F4")).padding(0, 1).render("rounded"),
        "  ",
        Style().border(THICK).border_foreground(Color("#FF7CCB")).padding(0, 1).render("thick"),
        "  ",
        Style().border(DOUBLE).border_foreground(Color("#FDFF8C")).padding(0, 1).render("double"),
    )
    return join_vertical(
        0.0, title, "", attrs, "", "badge " + badge + "   gradient " + swatch, "", boxes
    )


def layout() -> str:
    def card(t, body, color):
        head = (
            Style().bold().foreground(Color("#FAFAFA")).background(Color(color)).padding(0, 1).render(t)
        )
        return (
            Style().border(ROUNDED).border_foreground(Color(color)).padding(1, 2).width(18)
            .render(head + "\n\n" + body)
        )

    a = card("Red", "A short body.", "#FF5F87")
    b = card("Blue", "A longer body that wraps across lines.", "#5F87FF")
    c = card("Green", "Mid.", "#5FD787")
    title = Style().bold().foreground(Color("#7D56F4")).render("join_horizontal(TOP, ...)")
    return title + "\n\n" + join_horizontal(TOP, a, "  ", b, "  ", c)


def spinner_frames() -> list[str]:
    sp = Spinner(DOTS, Style().foreground(Color("#FF7CCB")))
    label = Style().faint().render(" Brewing your interface...")
    frames = []
    for i in range(len(DOTS.frames)):
        sp.frame = i
        frames.append("  " + sp.view() + label)
    return frames


def textinput() -> str:
    ti = TextInput()
    ti.prompt = "name › "
    ti.prompt_style = Style().foreground(Color("#7D56F4")).bold()
    ti.set_value("interrobang")
    ti.cursor = 4
    title = Style().bold().foreground(Color("#FF7CCB")).render("What's your name?")
    hint = Style().faint().render("enter submit · esc cancel")
    return "\n".join([title, "", ti.view(), "", hint])


def progress_frames() -> list[str]:
    bar = Progress(width=42).with_gradient("#FF7CCB", "#FDFF8C")
    label = Style().bold().render("Downloading interrobang...")
    return [label + "\n\n" + bar.view_as(k / 20) for k in range(21)]


def viewport() -> str:
    vp = Viewport(width=52, height=8)
    text = "\n".join(f"{i:>2}. The interrobang ‽ unites ? and !." for i in range(1, 25))
    vp.set_content(text)
    vp.scroll_down(4)
    frame = Style().border(ROUNDED).border_foreground(Color("#7D56F4")).render(vp.view())
    footer = Style().faint().render(f"{int(vp.scroll_percent() * 100)}% · ↑/↓ scroll · q quit")
    return frame + "\n" + footer


def listview() -> str:
    lst = List(SNACKS, width=44, height=14)
    lst.title = "Snacks"
    lst.cursor = 2
    return lst.view()


def table() -> str:
    t = Table(
        columns=[Column("Library", 16), Column("Language", 10), Column("Author", 16), Column("Stars", 6)],
        rows=TABLE_ROWS,
        height=10,
    )
    t.cursor = 4
    title = Style().bold().foreground(Color("#7D56F4")).render("TUI libraries")
    return title + "\n\n" + t.view()


def paginator() -> str:
    p = Paginator(per_page=8)
    p.set_total_items(47)
    p.page = 1
    start, end = p.slice_bounds(47)
    items = "\n".join(
        Style().foreground(Color("#DDDDDD")).render("  Item #%02d" % i) for i in range(start + 1, end + 1)
    )
    dots = Style().foreground(Color("#FF7CCB")).render(p.view())
    title = Style().bold().foreground(Color("#7D56F4")).render("Paginated items")
    return "\n".join([title, "", items, "", "  " + dots])


def helpview() -> str:
    up = KeyBinding(["up", "k"], "↑/k", "move up")
    down = KeyBinding(["down", "j"], "↓/j", "move down")
    left = KeyBinding(["left", "h"], "←/h", "move left")
    right = KeyBinding(["right", "l"], "→/l", "move right")
    quit_ = KeyBinding(["q"], "q", "quit")
    h = Help()
    title = Style().bold().foreground(Color("#7D56F4")).render("Help component")
    short = h.short_view([up, down, left, right, quit_])
    full = h.full_view([[up, down], [left, right], [quit_]])
    return "\n".join([title, "", "short help", "  " + short, "", "full help", full])


def filepicker() -> str:
    fp = FilePicker(path=ROOT, height=12)
    fp.cursor = 2
    title = Style().bold().foreground(Color("#7D56F4")).render("Pick a file")
    return title + "\n\n" + fp.view()


# --- driver -------------------------------------------------------------------

STILLS = {
    "hero": ("interrobang ‽", hero),
    "counter": ("counter.py", counter),
    "styling": ("styling", styling),
    "layout": ("layout", layout),
    "textinput": ("text input", textinput),
    "viewport": ("viewport", viewport),
    "list": ("list", listview),
    "table": ("table", table),
    "paginator": ("paginator", paginator),
    "help": ("help", helpview),
    "filepicker": ("file picker", filepicker),
}

ANIMATIONS = {
    "spinner": ("spinner", spinner_frames, 10.0),
    "progress": ("progress", progress_frames, 12.0),
}


def main() -> None:
    os.makedirs(IMAGES_DIR, exist_ok=True)
    for name, (title, fn) in STILLS.items():
        svg = render_svg(fn(), title)
        path = os.path.join(IMAGES_DIR, f"{name}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"wrote {os.path.relpath(path, ROOT)}  ({len(svg)} bytes)")

    for name, (title, fn, fps) in ANIMATIONS.items():
        svg = render_animated_svg(fn(), title, fps=fps)
        path = os.path.join(IMAGES_DIR, f"{name}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"wrote {os.path.relpath(path, ROOT)}  (animated, {len(svg)} bytes)")


if __name__ == "__main__":
    main()
