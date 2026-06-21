"""The :class:`Model` protocol -- the shape every interrobang app implements.

An application is three methods, the heart of the Elm Architecture:

* ``init()`` -- return an optional startup :data:`~interrobang.command.Command`.
* ``update(msg)`` -- given the current state and an incoming message, return the
  next state and an optional command. This is where all your logic lives, and
  it stays pure: no printing, no I/O, just state in and state out.
* ``view()`` -- render the current state to a string. The runtime paints it.

You do not have to subclass anything; any object with these methods works
(``Model`` is a :class:`typing.Protocol`). Subclassing :class:`Model` is still
handy for the default ``init`` and clear intent.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from .command import Command
    from .message import Msg

__all__ = ["Model"]


@runtime_checkable
class Model(Protocol):
    """The interface the runtime expects of your application state."""

    def init(self) -> "Command":
        """Return a command to run at startup, or ``None``."""
        return None

    def update(self, msg: "Msg") -> "tuple[Model, Command]":
        """Handle *msg*, returning ``(next_model, command)``.

        Return ``self`` (optionally after mutating it) or a brand-new model.
        The command may be ``None`` if there is nothing to do.
        """
        ...

    def view(self) -> str:
        """Render the current state to a string for display."""
        ...
