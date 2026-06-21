# Styling guide

interrobang's styling engine is its Lip Gloss analog. The centerpiece is
`Style`: an immutable, chainable description of how text should look and lay out.
You build a style with fluent setters and call `.render()` to turn text into an
ANSI-decorated string.

```python
from interrobang.style import Style, Color, ROUNDED

box = (
    Style()
    .bold()
    .foreground(Color("#FAFAFA"))
    .background(Color("#7D56F4"))
    .padding(1, 3)
    .border(ROUNDED)
)
print(box.render("Hello, there!"))
```

Because styles are immutable, every setter returns a **new** style. Define a
style once at module scope and reuse it everywhere — it's safe to share.

## Text attributes

| Setter | Effect |
| --- | --- |
| `.bold()` | bold |
| `.faint()` | dim |
| `.italic()` | italic |
| `.underline()` | underline |
| `.strikethrough()` | strikethrough |
| `.blink()` | blink |
| `.reverse()` | swap fg/bg |

Each takes an optional boolean, so `.bold(False)` turns it off:

```python
Style().bold().italic().render("important")
```

## Colors

There are several ways to specify a color, all accepted anywhere a color is
expected (you can pass a bare string or int and it's wrapped for you):

```python
from interrobang.style import Color, ANSIColor, AdaptiveColor, CompleteColor

Color("#7D56F4")     # 24-bit hex (or shorthand "#7cf")
Color(212)           # 256-color palette index
Color(5)             # one of the 16 base colors (0-15)
ANSIColor(5)         # explicitly one of the 16 base colors
Color.from_rgb(125, 86, 244)
```

### Profiles and automatic degradation

Terminals support different numbers of colors. interrobang models four
**profiles** and degrades colors down to whatever the terminal can show:

```
TRUECOLOR (24-bit) → ANSI256 (256) → ANSI (16) → ASCII (none)
```

A `#7D56F4` truecolor becomes the nearest 256-color, then the nearest of 16,
then nothing — automatically. You write the color once. The runtime detects the
profile from `$COLORTERM`/`$TERM` (and honors `$NO_COLOR`); you can override it:

```python
from interrobang.style import set_color_profile, Profile
set_color_profile(Profile.ANSI256)
```

Or pin a single style to a profile with `.color_profile(Profile.ANSI)`.

### Adaptive colors

`AdaptiveColor` chooses between two colors based on whether the terminal
background is dark or light:

```python
text = Style().foreground(AdaptiveColor(light="#1A1A1A", dark="#DDDDDD"))
```

### Complete colors

When you want exact control per profile (no automatic degradation),
`CompleteColor` lets you specify each:

```python
CompleteColor(true_color="#7D56F4", ansi256=99, ansi=5)
```

## Padding and margins

Padding is space *inside* the styled region (it carries the background color);
margin is space *outside* it. Both use CSS-style shorthand:

```python
Style().padding(1)           # 1 on all sides
Style().padding(1, 2)        # 1 vertical, 2 horizontal
Style().padding(1, 2, 3, 4)  # top, right, bottom, left
Style().padding_left(2)      # one side at a time
```

```python
Style().margin(0, 1).margin_background(Color("#000000"))
```

## Sizing and alignment

```python
Style().width(30)    # wrap content to 30 cells wide
Style().height(10)   # pad (or crop) the block to 10 lines tall
Style().max_width(40)   # truncate every line to 40 cells
Style().max_height(5)   # keep at most 5 lines
```

Alignment uses positions in `[0, 1]`; the constants `LEFT`/`CENTER`/`RIGHT` and
`TOP`/`BOTTOM` cover the common cases:

```python
from interrobang.style import Style, CENTER, BOTTOM

Style().width(20).align(CENTER).render("centered")
Style().height(5).align_vertical(BOTTOM).render("bottom")
```

## Borders

Pick a border preset or build your own:

```python
from interrobang.style import Style, NORMAL, ROUNDED, THICK, DOUBLE, ASCII, Border

Style().border(ROUNDED).render("rounded box")
Style().border(NORMAL, top=False).render("no top edge")  # partial borders
Style().border(ROUNDED).border_foreground(Color("#7D56F4")).render("colored")
```

Presets: `NORMAL`, `ROUNDED`, `THICK`, `DOUBLE`, `BLOCK`, `HIDDEN`, `ASCII`,
`MARKDOWN`. Build a custom one by constructing a `Border` with the glyphs you
want:

```python
star = Border(top="*", bottom="*", left="*", right="*",
              top_left="*", top_right="*", bottom_left="*", bottom_right="*")
Style().border(star).render("starry")
```

## Inline styling

`.inline()` ignores block layout (width, height, padding, margins, borders) and
applies only text attributes and colors — perfect for styling a span within a
line:

```python
prefix = Style().foreground(Color("#FF7CCB")).inline()
print(prefix.render("ERROR") + " something went wrong")
```

## Composing blocks: the layout helpers

Rendered blocks are just multi-line strings. The layout helpers arrange them,
measuring visible width correctly (they ignore ANSI escapes):

```python
from interrobang.style import join_horizontal, join_vertical, place, CENTER, TOP

# Side by side, top-aligned:
join_horizontal(TOP, left_block, "  ", right_block)

# Stacked, centered:
join_vertical(CENTER, "small", "a wider line", "mid")

# Center content inside a fixed box (e.g. the whole screen):
place(width, height, CENTER, CENTER, content)
```

Other helpers: `align_horizontal`, `align_vertical`, `place_horizontal`,
`place_vertical`, and `pad_right`.

### Centering on screen

Combine a `WindowSizeMsg` with `place` to center anything:

```python
def update(self, msg):
    if isinstance(msg, WindowSizeMsg):
        self.w, self.h = msg.width, msg.height
    return self, None

def view(self):
    card = Style().border(ROUNDED).padding(1, 2).render("Centered!")
    return place(self.w, self.h, CENTER, CENTER, card)
```

## Measuring text

When you do your own layout math, measure with cell-aware helpers (wide CJK
characters count as 2, combining marks as 0, ANSI escapes as 0):

```python
from interrobang import string_width, truncate, wrap, strip_ansi

string_width("世界")        # 4
truncate("hello world", 5, "…")  # "hell…"
wrap("the quick brown fox", 9)   # "the quick\nbrown fox"
strip_ansi("\x1b[1mhi\x1b[0m")   # "hi"
```

## Reading a style's metrics

Styles expose getters useful for layout calculations:

```python
s = Style().padding(1, 2).border(ROUNDED).margin(1)
s.horizontal_frame_size()  # padding + border + margin, horizontally
s.vertical_frame_size()
s.get_width(), s.get_height(), s.get_padding()
```

## Inheritance

`.inherit(other)` fills in any *unset* text attributes, colors, and border from
another style — handy for theming. Sizing, padding, and margins are deliberately
not inherited (they describe a specific layout, not a reusable look):

```python
base = Style().foreground(Color("#DDDDDD"))
heading = Style().bold().inherit(base)   # bold + inherited color
```
