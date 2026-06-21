"""A single-line text input field with a cursor, scrolling, and echo modes.

Embed it in your model and forward messages to it::

    class Model:
        def __init__(self):
            self.input = TextInput()
            self.input.placeholder = "Type something..."

        def update(self, msg):
            self.input, cmd = self.input.update(msg)
            return self, cmd

        def view(self):
            return self.input.view()

Read the typed text from :attr:`TextInput.value`.
"""

from __future__ import annotations

from enum import Enum, auto

from ..key import KeyMsg, KeyType
from ..style import Style
from .._ansi import string_width

__all__ = ["EchoMode", "TextInput"]


class EchoMode(Enum):
    """How typed characters are displayed."""

    NORMAL = auto()  #: Show characters as typed.
    PASSWORD = auto()  #: Show a masking character instead of each character.
    NONE = auto()  #: Show nothing at all.


class TextInput:
    """An editable single-line text field."""

    def __init__(self):
        self.value: str = ""
        self.cursor: int = 0
        self.prompt: str = "> "
        self.placeholder: str = ""
        self.focused: bool = True
        self.char_limit: int = 0  # 0 = unlimited
        self.width: int = 0  # 0 = unlimited (no horizontal scrolling)
        self.echo: EchoMode = EchoMode.NORMAL
        self.echo_char: str = "•"
        self.prompt_style: Style = Style()
        self.text_style: Style = Style()
        self.placeholder_style: Style = Style().faint()
        self.cursor_style: Style = Style().reverse()

    # -- state helpers -----------------------------------------------------

    def focus(self) -> None:
        """Give the field focus so it accepts keystrokes."""
        self.focused = True

    def blur(self) -> None:
        """Remove focus; keystrokes are ignored until refocused."""
        self.focused = False

    def reset(self) -> None:
        """Clear the value and move the cursor home."""
        self.value = ""
        self.cursor = 0

    def set_value(self, value: str) -> None:
        """Replace the value, honoring ``char_limit``, cursor at the end."""
        if self.char_limit > 0:
            value = value[: self.char_limit]
        self.value = value
        self.cursor = len(value)

    # -- update ------------------------------------------------------------

    def update(self, msg: object) -> "tuple[TextInput, None]":
        """Handle a key message, editing the value in place."""
        if not self.focused or not isinstance(msg, KeyMsg):
            return self, None

        key = msg.key
        if msg.type is KeyType.RUNES and not msg.ctrl and not msg.alt:
            self._insert(msg.runes)
        elif msg.type is KeyType.SPACE:
            self._insert(" ")
        elif key == "left":
            self.cursor = max(0, self.cursor - 1)
        elif key == "right":
            self.cursor = min(len(self.value), self.cursor + 1)
        elif key in ("home", "ctrl+a"):
            self.cursor = 0
        elif key in ("end", "ctrl+e"):
            self.cursor = len(self.value)
        elif key == "backspace":
            if self.cursor > 0:
                self.value = self.value[: self.cursor - 1] + self.value[self.cursor :]
                self.cursor -= 1
        elif key == "delete":
            if self.cursor < len(self.value):
                self.value = self.value[: self.cursor] + self.value[self.cursor + 1 :]
        elif key == "ctrl+u":  # delete to start of line
            self.value = self.value[self.cursor :]
            self.cursor = 0
        elif key == "ctrl+k":  # delete to end of line
            self.value = self.value[: self.cursor]
        elif key == "ctrl+w":  # delete previous word
            self._delete_word()
        return self, None

    def _insert(self, text: str) -> None:
        if self.char_limit > 0 and len(self.value) + len(text) > self.char_limit:
            text = text[: self.char_limit - len(self.value)]
        if not text:
            return
        self.value = self.value[: self.cursor] + text + self.value[self.cursor :]
        self.cursor += len(text)

    def _delete_word(self) -> None:
        if self.cursor == 0:
            return
        i = self.cursor
        while i > 0 and self.value[i - 1] == " ":
            i -= 1
        while i > 0 and self.value[i - 1] != " ":
            i -= 1
        self.value = self.value[:i] + self.value[self.cursor :]
        self.cursor = i

    # -- view --------------------------------------------------------------

    def _display_value(self) -> str:
        if self.echo is EchoMode.PASSWORD:
            return self.echo_char * len(self.value)
        if self.echo is EchoMode.NONE:
            return ""
        return self.value

    def view(self) -> str:
        """Render the prompt, the (possibly masked) text, and the cursor."""
        prompt = self.prompt_style.render(self.prompt)

        if not self.value and self.placeholder:
            return prompt + self._render_placeholder()

        display = self._display_value()
        cursor_pos = self.cursor if self.echo is not EchoMode.NONE else len(display)
        body = self._render_with_cursor(display, cursor_pos)
        return prompt + body

    def _render_placeholder(self) -> str:
        if not self.placeholder:
            return ""
        if self.focused:
            first = self.cursor_style.render(self.placeholder[0])
            rest = self.placeholder_style.render(self.placeholder[1:])
            return first + rest
        return self.placeholder_style.render(self.placeholder)

    def _render_with_cursor(self, display: str, cursor_pos: int) -> str:
        # Window the text horizontally so the cursor stays visible.
        start = 0
        if self.width > 0 and string_width(display) >= self.width:
            if cursor_pos >= self.width:
                start = cursor_pos - self.width + 1
            end = start + self.width
            visible = display[start:end]
            local_cursor = cursor_pos - start
        else:
            visible = display
            local_cursor = cursor_pos

        if not self.focused:
            return self.text_style.render(visible)

        before = self.text_style.render(visible[:local_cursor])
        if local_cursor < len(visible):
            at = self.cursor_style.render(visible[local_cursor])
            after = self.text_style.render(visible[local_cursor + 1 :])
        else:
            at = self.cursor_style.render(" ")
            after = ""
        return before + at + after
