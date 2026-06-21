"""Helpers for testing interrobang apps without a real terminal.

Because ``update`` is pure, you can verify an app's behavior by feeding it
messages and inspecting the resulting state and views -- no TTY, no threads, no
flakiness. :func:`feed` does exactly that. :func:`run_command` executes a
command synchronously so you can assert on the message it produces, and
:func:`drive` runs the *real* event loop headlessly for integration tests.
"""

from __future__ import annotations

import io
import threading
from dataclasses import dataclass
from typing import Iterable

from ._ansi import strip_ansi
from .command import BatchCmd, Command, SequenceCmd
from .message import Msg
from .model import Model
from .program import Program

__all__ = ["StepResult", "feed", "run_command", "drive", "strip_ansi"]


@dataclass
class StepResult:
    """The outcome of applying one message: the new model, command, and view."""

    model: Model
    command: Command
    view: str


def feed(model: Model, messages: Iterable[Msg]) -> list[StepResult]:
    """Apply *messages* to *model* in order, returning one result per message.

    This drives only ``update`` and ``view`` -- no commands are executed -- so it
    is completely deterministic. Inspect ``results[-1].model`` for the final
    state, or ``results[i].command`` to assert what command step *i* requested::

        results = feed(Counter(), [KeyMsg(KeyType.RUNES, "+")])
        assert results[-1].model.count == 1
    """
    results: list[StepResult] = []
    current = model
    for msg in messages:
        outcome = current.update(msg)
        if isinstance(outcome, tuple):
            current, command = outcome
        else:
            current, command = outcome, None
        results.append(StepResult(current, command, current.view()))
    return results


def run_command(command: Command) -> list[Msg]:
    """Execute *command* synchronously and collect the messages it yields.

    Batches and sequences are flattened (run in order, on this thread), so this
    is convenient for asserting what a command does -- but note that timer
    commands like :func:`~interrobang.tick` really will sleep.
    """
    out: list[Msg] = []

    def go(cmd: Command) -> None:
        if cmd is None:
            return
        if isinstance(cmd, (BatchCmd, SequenceCmd)):
            for child in cmd.cmds:
                go(child)
            return
        msg = cmd()
        if msg is not None:
            out.append(msg)

    go(command)
    return out


def drive(model: Model, messages: Iterable[Msg], *, alt_screen: bool = False) -> tuple[str, Model]:
    """Run the real event loop headlessly, sending *messages*, then quitting.

    Returns ``(raw_output, final_model)``. The output contains the actual escape
    sequences the renderer produced; wrap it with :func:`strip_ansi` if you want
    to assert on visible text. Use this to integration-test the loop, control
    commands, and rendering; use :func:`feed` for pure update/view logic.
    """
    output = io.StringIO()
    program = Program(model, output=output, headless=True, alt_screen=alt_screen, catch_interrupt=False)
    thread = threading.Thread(target=program.run)
    thread.start()
    for msg in messages:
        program.send(msg)
    program.quit()
    thread.join(timeout=5.0)
    return output.getvalue(), program.final_model
