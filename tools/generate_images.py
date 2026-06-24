"""Generate the documentation screenshots in docs/images/.

Each image is produced from the *real* output of interrobang's styling engine
and components under the active :class:`~interrobang.theme.Theme`, then rendered
to an SVG terminal window by ``tools/termshot``. Run it from anywhere:

    python tools/generate_images.py

The terminal chrome and component accents both follow the active theme, so to
re-render the docs under a different theme you only change ``set_theme(...)``
below. Regenerate after changing component visuals so the docs stay accurate.
"""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import termshot  # noqa: E402

from interrobang import CHARM, SOLARIZED_DARK, SOLARIZED_LIGHT, get_theme, set_theme  # noqa: E402
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
    Profile,
    Style,
    join_horizontal,
    join_vertical,
    set_color_profile,
    set_has_dark_background,
)

# --- active theme -------------------------------------------------------------
set_color_profile(Profile.TRUECOLOR)
set_has_dark_background(True)
set_theme(SOLARIZED_DARK)
T = get_theme()

# Point the screenshot chrome at the theme's surfaces.
termshot.BG = T.background
termshot.TITLEBAR = T.surface
termshot.FG = T.text
termshot.TITLE_FG = T.muted
termshot.TRAFFIC = (
    ("#dc322f", "#b58900", "#859900")
    if T.name == "Solarized Dark"
    else ("#ff5f56", "#febc2e", "#28c840")
)

from termshot import render_animated_svg, render_svg  # noqa: E402

IMAGES_DIR = os.path.join(ROOT, "docs", "images")

MARKS = [
    Item("Interrobang", "‽  asks and exclaims at once"),
    Item("Exclamation point", "!  emphatic and eager"),
    Item("Question mark", "?  curious and uncertain"),
    Item("Em dash", "—  an abrupt aside"),
    Item("Ellipsis", "…  a trailing off"),
    Item("Semicolon", ";  joins two related clauses"),
]

TABLE_ROWS = [
    ["‽", "Interrobang", "U+203D", "1962"],
    ["!", "Exclamation point", "U+0021", "1400s"],
    ["?", "Question mark", "U+003F", "1500s"],
    ["—", "Em dash", "U+2014", "—"],
    ["…", "Ellipsis", "U+2026", "—"],
    ["&", "Ampersand", "U+0026", "~50 BC"],
]


def header(text: str) -> str:
    return Style().bold().foreground(T.on_primary).background(T.primary).padding(0, 2).render(text)


# --- subjects -----------------------------------------------------------------


def hero() -> str:
    sp = Spinner(DOTS)
    sp.frame = 2
    bar = Progress(width=30)
    lst = List(
        [Item(t) for t in ("Fetch deps", "Compile", "Run tests", "Build", "Package", "Publish")],
        width=26,
        height=10,
    )
    lst.title = "Pipeline"
    lst.show_description = False
    lst.show_status_bar = False
    lst.cursor = 2

    status_panel = Style().border(ROUNDED).border_foreground(T.secondary).padding(1, 2).width(34)
    status_body = join_vertical(
        0.0, f"{sp.view()} working...", "", "Build progress:", bar.view_as(0.6)
    )
    list_panel = Style().border(ROUNDED).border_foreground(T.faint).padding(1, 2)
    panels = join_horizontal(TOP, status_panel.render(status_body), "  ", list_panel.render(lst.view()))
    footer = Style().foreground(T.muted).render("↑/↓ move the list · q quit")
    return "\n".join([header("interrobang dashboard ‽"), "", panels, "", footer])


def counter() -> str:
    title = Style().bold().foreground(T.primary).render("interrobang counter")
    number = Style().bold().foreground(T.on_primary).background(T.primary).padding(0, 2).render("42")
    hint = Style().foreground(T.muted).render("↑/↓ change · q quit")
    return "\n".join([title, "", "  " + number, "", hint])


def styling() -> str:
    title = Style().bold().foreground(T.primary).render("Styling gallery")
    attrs = "   ".join(
        [
            Style().bold().render("bold"),
            Style().italic().render("italic"),
            Style().underline().render("underline"),
            Style().strikethrough().render("strike"),
            Style().reverse().render(" reverse "),
        ]
    )
    badge = Style().bold().foreground(T.on_selection).background(T.selection).padding(0, 2).render("NEW")
    bar = Progress(width=22)
    bar.show_percentage = False
    swatch = bar.view_as(1.0)
    boxes = join_horizontal(
        TOP,
        Style().border(ROUNDED).border_foreground(T.secondary).padding(0, 1).render("rounded"),
        "  ",
        Style().border(THICK).border_foreground(T.selection).padding(0, 1).render("thick"),
        "  ",
        Style().border(DOUBLE).border_foreground(T.primary).padding(0, 1).render("double"),
    )
    return join_vertical(
        0.0, title, "", attrs, "", "badge " + badge + "   gradient " + swatch, "", boxes
    )


def layout() -> str:
    def card(name, body, color):
        head = Style().bold().foreground(T.on_primary).background(color).padding(0, 1).render(name)
        return (
            Style().border(ROUNDED).border_foreground(color).padding(1, 2).width(18)
            .render(head + "\n\n" + body)
        )

    a = card("Blue", "A short body.", T.primary)
    b = card("Violet", "A longer body that wraps across lines.", T.secondary)
    c = card("Green", "Mid.", T.gradient_end)
    title = Style().bold().foreground(T.primary).render("join_horizontal(TOP, ...)")
    return title + "\n\n" + join_horizontal(TOP, a, "  ", b, "  ", c)


def spinner_frames() -> list[str]:
    sp = Spinner(DOTS)
    label = Style().foreground(T.muted).render(" Asking the important questions ‽")
    frames = []
    for i in range(len(DOTS.frames)):
        sp.frame = i
        frames.append("  " + sp.view() + label)
    return frames


def textinput() -> str:
    ti = TextInput()
    ti.prompt = "name › "
    ti.set_value("interrobang")
    ti.cursor = 4
    title = Style().bold().foreground(T.selection).render("What's your name?")
    hint = Style().foreground(T.muted).render("enter submit · esc cancel")
    return "\n".join([title, "", ti.view(), "", hint])


def progress_frames() -> list[str]:
    bar = Progress(width=42)
    label = Style().bold().render("Downloading interrobang...")
    return [label + "\n\n" + bar.view_as(k / 20) for k in range(21)]


def viewport() -> str:
    vp = Viewport(width=52, height=8)
    text = "\n".join(f"{i:>2}. The interrobang ‽ unites ? and !." for i in range(1, 25))
    vp.set_content(text)
    vp.scroll_down(4)
    frame = Style().border(ROUNDED).border_foreground(T.secondary).render(vp.view())
    footer = Style().foreground(T.muted).render(f"{int(vp.scroll_percent() * 100)}% · ↑/↓ scroll · q quit")
    return frame + "\n" + footer


def listview() -> str:
    lst = List(MARKS, width=44, height=14)
    lst.title = "Punctuation"
    lst.cursor = 2
    return lst.view()


def table() -> str:
    t = Table(
        columns=[Column("Mark", 5), Column("Name", 18), Column("Unicode", 9), Column("Coined", 8)],
        rows=TABLE_ROWS,
        height=10,
    )
    t.cursor = 0
    title = Style().bold().foreground(T.primary).render("Punctuation marks")
    return title + "\n\n" + t.view()


def paginator() -> str:
    p = Paginator(per_page=8)
    p.set_total_items(47)
    p.page = 1
    start, end = p.slice_bounds(47)
    items = "\n".join(Style().render("  Item #%02d" % i) for i in range(start + 1, end + 1))
    title = Style().bold().foreground(T.primary).render("Paginated items")
    return "\n".join([title, "", items, "", "  " + p.view()])


def helpview() -> str:
    up = KeyBinding(["up", "k"], "↑/k", "move up")
    down = KeyBinding(["down", "j"], "↓/j", "move down")
    left = KeyBinding(["left", "h"], "←/h", "move left")
    right = KeyBinding(["right", "l"], "→/l", "move right")
    quit_ = KeyBinding(["q"], "q", "quit")
    h = Help()
    title = Style().bold().foreground(T.primary).render("Help component")
    short = h.short_view([up, down, left, right, quit_])
    full = h.full_view([[up, down], [left, right], [quit_]])
    return "\n".join([title, "", "short help", "  " + short, "", "full help", full])


def filepicker() -> str:
    fp = FilePicker(path=ROOT, height=12)
    fp.cursor = 2
    title = Style().bold().foreground(T.primary).render("Pick a file")
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

THEME_PREVIEWS = {
    "theme-solarized-dark": SOLARIZED_DARK,
    "theme-solarized-light": SOLARIZED_LIGHT,
    "theme-charm": CHARM,
}


def theme_panel(theme) -> str:
    """A compact panel (spinner + progress + list) rendered in *theme*."""
    sp = Spinner(DOTS)
    sp.frame = 2
    bar = Progress(width=24)
    lst = List([Item("Alpha"), Item("Beta"), Item("Gamma")], width=24, height=8)
    lst.show_description = False
    lst.show_status_bar = False
    lst.cursor = 1
    title = (
        Style().bold().foreground(theme.on_primary).background(theme.primary).padding(0, 1)
        .render(f" {theme.name} ")
    )
    body = join_vertical(0.0, f"{sp.view()} loading...", "", bar.view_as(0.6), "", lst.view())
    return title + "\n\n" + body


def _set_chrome(theme) -> None:
    termshot.BG = theme.background
    termshot.TITLEBAR = theme.surface
    termshot.FG = theme.text
    termshot.TITLE_FG = theme.muted
    termshot.TRAFFIC = (
        ("#dc322f", "#b58900", "#859900")
        if theme.name.startswith("Solarized")
        else ("#ff5f56", "#febc2e", "#28c840")
    )


def main() -> None:
    os.makedirs(IMAGES_DIR, exist_ok=True)
    print(f"Theme: {T.name}")
    for name, (title, fn) in STILLS.items():
        svg = render_svg(fn(), title)
        with open(os.path.join(IMAGES_DIR, f"{name}.svg"), "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"wrote docs/images/{name}.svg  ({len(svg)} bytes)")
    for name, (title, fn, fps) in ANIMATIONS.items():
        svg = render_animated_svg(fn(), title, fps=fps)
        with open(os.path.join(IMAGES_DIR, f"{name}.svg"), "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"wrote docs/images/{name}.svg  (animated, {len(svg)} bytes)")

    for name, theme in THEME_PREVIEWS.items():
        set_theme(theme)
        _set_chrome(theme)
        svg = render_svg(theme_panel(theme), theme.name)
        with open(os.path.join(IMAGES_DIR, f"{name}.svg"), "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"wrote docs/images/{name}.svg  ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
