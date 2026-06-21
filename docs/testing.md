# Testing guide

A core promise of the Elm Architecture is testability: because `update` is pure,
you can verify your app's behavior by feeding it messages and inspecting the
results — no terminal, no threads, no flakiness. interrobang gives you three
helpers in `interrobang.testing`.

## `feed` — drive update/view directly

`feed(model, messages)` applies each message through `update` in order and
returns one `StepResult` per message. Each result has `.model` (the state after
that step), `.command` (what that step requested), and `.view` (the rendered
string).

```python
from interrobang.testing import feed
from interrobang import KeyMsg, KeyType

def test_counter_increments():
    results = feed(Counter(), [KeyMsg(KeyType.UP), KeyMsg(KeyType.UP)])
    assert results[-1].model.count == 2
    assert "2" in results[-1].view
```

This is the workhorse: it's fully deterministic and runs no commands, so it's
ideal for unit-testing your state logic.

### Asserting on commands

`feed` captures the command each step returned, so you can assert what your app
*asked* the runtime to do:

```python
from interrobang import quit

def test_q_quits():
    results = feed(App(), [KeyMsg(KeyType.RUNES, "q")])
    assert results[-1].command is quit
```

## `run_command` — execute a command

To check what a command actually produces, run it synchronously with
`run_command`. It flattens `batch`/`sequence` and returns the list of messages
yielded:

```python
from interrobang.testing import run_command
from interrobang import batch

def test_command_loads_data():
    msgs = run_command(my_load_command)
    assert isinstance(msgs[0], DataLoaded)

def test_batch():
    assert run_command(batch(lambda: "a", lambda: "b")) == ["a", "b"]
```

> Timer commands (`tick`, `every`) really do sleep when run, so prefer asserting
> that `update` *returned* a tick (via `feed`) over executing it.

## `drive` — run the real event loop headlessly

For integration tests, `drive(model, messages)` runs the actual `Program` loop
with in-memory I/O, sends your messages, then quits. It returns the raw rendered
output and the final model — exercising the loop, command execution, control
messages, and the renderer.

```python
from interrobang.testing import drive, strip_ansi

def test_full_loop():
    output, final = drive(App(), [KeyMsg(KeyType.RUNES, "+")])
    assert final.count == 1
    assert "count=1" in strip_ansi(output)
```

The output contains real escape sequences; wrap it with `strip_ansi` to assert
on visible text. Pass `alt_screen=True` to test alt-screen rendering.

## Testing components

Components are models too, so the same helpers work. Drive a component's
`update` directly:

```python
from interrobang.components import TextInput

def press(ti, key):
    return ti.update(key)[0]

def test_typing():
    ti = TextInput()
    for ch in "hello":
        ti = press(ti, KeyMsg(KeyType.RUNES, ch))
    assert ti.value == "hello"
```

## Pinning the color profile

Style output depends on the active color profile. In tests, pin it so results
are identical everywhere (this is exactly what interrobang's own test suite does
in `conftest.py`):

```python
import pytest
from interrobang.style import Profile, set_color_profile, set_has_dark_background

@pytest.fixture(autouse=True)
def deterministic_color():
    set_color_profile(Profile.TRUECOLOR)
    set_has_dark_background(True)
    yield
```

Or sidestep colors entirely by asserting on `strip_ansi(view)`.

## Running interrobang's own suite

```bash
pip install -e ".[dev]"
pytest                       # run everything
pytest --cov=interrobang --cov-report=term-missing   # with coverage
```

The suite covers the ANSI/width engine, the full style and color system,
borders and layout, key/mouse parsing, commands, the renderer, the event loop
(including a real-PTY test), every component, and even the examples — so the
examples can't silently fall out of sync with the library.
