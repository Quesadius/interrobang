# Components reference

Components are interrobang's ready-made widgets — the Bubbles analog. Each is a
small self-contained model with its own `update` and `view`, plus configuration
attributes and helper methods. You embed one (or several) in your application
model, forward messages to it, and place its `view()` output wherever you like.

The universal pattern is:

```python
self.component, cmd = self.component.update(msg)
return self, cmd
```

Import them from `interrobang.components`:

```python
from interrobang.components import (
    Spinner, DOTS, TextInput, Progress, Viewport,
    List, Item, Table, Column, Paginator, KeyBinding, Help, FilePicker,
)
```

Every component has a runnable example in [`examples/`](../examples).

---

## Spinner

An animated activity indicator. Drive it by returning its `tick` command from
`init` and again whenever you receive a `SpinnerTickMsg`.

```python
from interrobang.components import Spinner, DOTS

class Model:
    def __init__(self):
        self.spinner = Spinner(DOTS)
    def init(self):
        return self.spinner.tick
    def update(self, msg):
        self.spinner, cmd = self.spinner.update(msg)
        return self, cmd
    def view(self):
        return f"{self.spinner.view()} loading..."
```

**Presets:** `LINE`, `DOTS`, `MINI_DOT`, `JUMP`, `PULSE`, `POINTS`, `GLOBE`,
`MOON`, `MONKEY`, `METER`, `HAMBURGER`, `ELLIPSIS`. Pass a `Style` as the second
argument to color it. Build your own with `SpinnerStyle(frames, fps)`.

---

## TextInput

A single-line editable field with a cursor, horizontal scrolling, and echo
modes.

```python
from interrobang.components import TextInput, EchoMode

inp = TextInput()
inp.placeholder = "your name"
inp.prompt = "› "
inp.char_limit = 50          # 0 = unlimited
inp.width = 30               # 0 = no horizontal scrolling
inp.echo = EchoMode.PASSWORD # NORMAL | PASSWORD | NONE
```

Read the text from `inp.value`. Methods: `focus()`, `blur()`, `reset()`,
`set_value(s)`. Supported keys: left/right, home/end (`ctrl+a`/`ctrl+e`),
backspace/delete, `ctrl+u` (delete to start), `ctrl+k` (delete to end),
`ctrl+w` (delete word). Style via `prompt_style`, `text_style`,
`placeholder_style`, `cursor_style`.

---

## Progress

A horizontal progress bar, solid or gradient.

```python
from interrobang.components import Progress

bar = Progress(width=40).with_gradient("#FF7CCB", "#FDFF8C")
print(bar.view_as(0.62))         # render at an explicit percentage

bar.set_percent(0.5)             # or store it and animate
bar.incr_percent(0.01)
print(bar.view())
```

Use `.with_solid("#7D56F4")` for a single color. Toggle the trailing percentage
with `show_percentage`. Customize `full_char`, `empty_char`, `percent_style`,
`empty_style`. Animate it by returning a `tick` command and calling
`incr_percent` each frame (see `examples/progress.py`).

---

## Viewport

A fixed-size scrollable window over multi-line text.

```python
from interrobang.components import Viewport

vp = Viewport(width=70, height=20)
vp.set_content(long_text)
vp, cmd = vp.update(msg)   # handles arrows, j/k, PgUp/PgDn, g/G, mouse wheel
print(vp.view())
```

Methods: `scroll_up/down(n)`, `page_up/down()`, `half_page_up/down()`,
`goto_top/bottom()`. Properties: `at_top`, `at_bottom`, `scroll_percent()`,
`total_lines`. The `view()` is always exactly `width` × `height`.

---

## List

A scrollable, selectable, filterable list. Items can be the provided `Item`
(a `title` and optional `description`) or any object exposing `title`/
`description`.

```python
from interrobang.components import List, Item

lst = List([Item("Pocky", "snack"), Item("Ramen", "soup")], width=40, height=14)
lst.title = "Snacks"
lst, cmd = lst.update(msg)
chosen = lst.selected_item()
```

Keys: up/down (j/k), home/end (g/G), `/` to filter (type to narrow, enter to
confirm, esc to clear). Configure `show_description`, `show_status_bar`,
`filter_enabled`, and the various styles. Replace items with `set_items(items)`.

---

## Table

A scrollable grid with a header and row selection.

```python
from interrobang.components import Table, Column

table = Table(
    columns=[Column("Name", 16), Column("Language", 10), Column("Stars", 6)],
    rows=[["bubbletea", "Go", "29k"], ["interrobang", "Python", "1"]],
    height=10,
)
table, cmd = table.update(msg)   # up/down (j/k), home/end (g/G)
row = table.selected_row()
```

Cells are truncated/padded to each `Column.width`. Replace rows with
`set_rows(rows)`. Style via `header_style`, `selected_style`, `cell_style`; set
`focused = False` to ignore navigation keys.

---

## Paginator

Pagination math plus a compact page indicator.

```python
from interrobang.components import Paginator, PaginatorType

p = Paginator(per_page=10)
p.set_total_items(95)                 # -> 10 pages
start, end = p.slice_bounds(95)       # indices for the current page
p, cmd = p.update(msg)                # ←/→ (h/l) change page
print(p.view())                       # ● ○ ○ ...  (or "1/10" with ARABIC)
```

Helpers: `next_page()`, `prev_page()`, `on_first_page`, `on_last_page`,
`items_on_page(total)`. Set `type = PaginatorType.ARABIC` for an `N/M` counter.

---

## KeyBinding & Help

Declarative key bindings with an auto-generated help view.

```python
from interrobang.components import KeyBinding, Help

up = KeyBinding(["up", "k"], "↑/k", "move up")
quit_ = KeyBinding(["q", "ctrl+c"], "q", "quit")

def update(self, msg):
    if quit_.matches(msg):
        return self, irb.quit
    ...

help = Help()
print(help.short_view([up, quit_]))            # ↑/k move up · q quit
print(help.full_view([[up], [quit_]]))         # multi-column table
```

`KeyBinding.matches(msg)` returns true for an enabled binding when `msg.key` is
one of its keys. Disable a binding with `set_enabled(False)` and it stops
matching and disappears from help. Toggle `Help.show_all` to switch between the
short and full views via `help.view(bindings)`.

---

## FilePicker

A filesystem browser for choosing a file (or directory).

```python
from interrobang.components import FilePicker

picker = FilePicker(path="~/Documents", height=15)
picker, cmd = picker.update(msg)
chosen = picker.did_select_file()   # path once the user picks, else None
if chosen:
    ...
```

Keys: up/down (j/k), enter/→ (open a directory or select a file),
backspace/← (go up), `.` (toggle hidden files). Set `dir_allowed = True` to let
Enter select a directory rather than descend into it. Directories sort first.
`did_select_file()` returns the chosen path once and then clears it.

---

## Building your own component

There's nothing special about the built-in components — they're ordinary objects
with `update(msg) -> (self, cmd)` and `view() -> str`. Follow the same shape and
your component composes with everything else, including the testing helpers.
