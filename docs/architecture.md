# The Elm Architecture

interrobang's runtime is a faithful, Pythonic take on **The Elm Architecture**
(TEA) — model, update, view. Once it clicks, building TUIs becomes almost
mechanical. This guide explains every piece.

## The big picture

```
        ┌─────────────┐   message    ┌──────────────┐
input ─▶│   runtime   │─────────────▶│    update    │
events  │ (Program)   │              │ (your logic) │
        │             │◀─────────────│              │
        └─────────────┘ model + cmd  └──────────────┘
              │                              │
              │ runs the command            │
              ▼                              │
        ┌─────────────┐   message           │
        │   command   │─────────────────────┘
        │ (side effect)│
        └─────────────┘
              │
              ▼  calls view(model), paints the screen
```

The loop never varies:

1. Something happens → the runtime makes a **message**.
2. The runtime calls **`update(msg)`**, which returns a new **model** and an
   optional **command**.
3. The runtime runs the command (often on a background thread); whatever
   message it produces goes back to step 2.
4. The runtime calls **`view()`** and paints the result.

Your `update` is **pure**: same model + same message → same result, with no I/O.
All side effects are pushed out into commands. That purity is what makes the
whole thing predictable and testable.

## Messages

A message is *any* Python object. The runtime produces a few built-ins:

| Message | When |
| --- | --- |
| `KeyMsg` | a key was pressed |
| `MouseMsg` | a mouse event (if mouse reporting is on) |
| `WindowSizeMsg` | at startup and on every resize |
| `QuitMsg` | the program is shutting down |

Your own messages are just classes you define — a frozen `dataclass` is ideal:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class DataLoaded:
    rows: list

@dataclass(frozen=True)
class TickMsg:
    t: float
```

You dispatch on type in `update`:

```python
def update(self, msg):
    if isinstance(msg, KeyMsg):
        ...
    elif isinstance(msg, DataLoaded):
        self.rows = msg.rows
    return self, None
```

### Keys in detail

`KeyMsg` carries a `type` (a `KeyType`), the typed `runes`, and `alt`/`ctrl`/
`shift` flags. The easiest way to react is its canonical name via `msg.key`:

```python
if msg.key == "ctrl+c": ...
if msg.key == "enter": ...
if msg.key == "shift+tab": ...
if msg.type is KeyType.RUNES:   # a printable character
    self.buffer += msg.runes
```

Names look like `"a"`, `"A"`, `"enter"`, `"ctrl+c"`, `"alt+left"`,
`"shift+tab"` — modifiers first, in `ctrl+alt+shift` order.

## The model

The model is your application state. It can be any object that implements
`update` and `view` (and optionally `init`). Use a plain class, a dataclass,
whatever you like. The runtime keeps whatever `update` returns and feeds it the
next message.

## Commands

A **command** is how `update` asks for a side effect without performing one. It's
just a zero-argument callable that returns a message (or `None`):

```python
def load_data():           # this is a command
    rows = fetch_from_db()  # the side effect happens here, off the main loop
    return DataLoaded(rows)

def update(self, msg):
    if msg.key == "r":
        return self, load_data   # return it; the runtime runs it for you
    ...
```

The runtime runs `load_data` on a background thread, so a slow command never
freezes your UI. When it finishes, `DataLoaded(rows)` flows back into `update`.

### Built-in commands

| Command | Effect |
| --- | --- |
| `quit` | stop the program |
| `batch(*cmds)` | run several commands **concurrently** |
| `sequence(*cmds)` | run several commands **in order** |
| `tick(seconds, fn)` | after a delay, call `fn(now)` to make a message |
| `every(seconds, fn)` | like `tick`, aligned to the wall clock |

`batch` and `sequence` let you fire off more than one effect:

```python
from interrobang import batch, tick

def init(self):
    return batch(self.spinner.tick, load_data)
```

### Timers

Timers are commands, and they don't repeat on their own — you re-issue them. This
keeps control in your hands:

```python
from dataclasses import dataclass
from interrobang import tick

@dataclass(frozen=True)
class TickMsg:
    t: float

def init(self):
    return tick(1.0, TickMsg)          # fire once after 1s

def update(self, msg):
    if isinstance(msg, TickMsg):
        self.seconds += 1
        return self, tick(1.0, TickMsg)  # schedule the next tick
    return self, None
```

`fn` receives the current wall-clock time; pass a class like `TickMsg` (it's
called as `TickMsg(now)`) or a lambda such as `lambda t: TickMsg(t)`.

### Terminal-control commands

Some commands tell the *terminal* to do something. They're returned from
`update` like any other command:

| Command | Effect |
| --- | --- |
| `enter_alt_screen` / `exit_alt_screen` | switch screen buffers |
| `hide_cursor` / `show_cursor` | cursor visibility |
| `enable_mouse` / `disable_mouse` | mouse reporting |
| `enable_background_fill` / `disable_background_fill` | toggle the theme background fill (alt screen) |
| `clear_screen` | force a full repaint |
| `set_window_title(title)` | set the terminal title |

These never reach your `update` — the runtime intercepts and performs them.

### Error handling

If a command raises, the runtime restores the terminal cleanly and then
re-raises the exception, so a bug in a background task can't leave your terminal
in raw mode. Handle expected failures by catching them inside the command and
returning an error *message* your `update` can react to.

## Running a program

```python
import interrobang as irb

irb.run(model, alt_screen=True, mouse=False)
# equivalently:
program = irb.Program(model, alt_screen=True)
final_model = program.run()
```

`Program` options:

| Option | Meaning |
| --- | --- |
| `alt_screen` | use the alternate screen buffer |
| `mouse` | enable mouse reporting |
| `input` / `output` | streams (default stdin/stdout; override for tests) |
| `headless` | skip raw mode, cursor, and signal handling |
| `catch_interrupt` | if true (default), Ctrl+C quits instead of reaching `update` |
| `fill_background` | paint the active theme's background across the alt screen (see the [styling guide](styling.md#theming-the-whole-screen)) |

`run()` blocks until the program quits, then returns the final model — handy for
reading a result out of, say, a prompt.

### Sending messages from outside

`program.send(msg)` is thread-safe, so external events (a websocket, a watcher)
can inject messages into the loop:

```python
program = irb.Program(model)
threading.Thread(target=lambda: watch(program)).start()
program.run()
```

## Lifecycle summary

1. The runtime configures the terminal (raw mode, alt screen, cursor, mouse).
2. It detects the color profile and dark/light background and configures the
   styling engine accordingly.
3. It runs `init()`'s command and sends an initial `WindowSizeMsg`.
4. It enters the loop: read message → `update` → run command → `view` → paint.
5. On `QuitMsg` (or Ctrl+C, by default), it restores the terminal and returns
   the final model.

That's the entire runtime. Everything else — components, styling — is built on
top of this loop.
