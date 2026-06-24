"""Ready-made widgets.

Each component is a small self-contained model: it has its own ``update`` and
``view``, plus configuration attributes and helper methods. You embed one (or
several) in your application model, forward messages to it, and place its
``view()`` output wherever you like.

Available components:

* :class:`Spinner` -- animated activity indicator
* :class:`TextInput` -- single-line editable field
* :class:`Progress` -- horizontal progress bar (solid or gradient)
* :class:`Viewport` -- scrollable text window
* :class:`List` -- selectable, filterable list
* :class:`Table` -- scrollable grid with row selection
* :class:`Paginator` -- pagination math and a page indicator
* :class:`KeyBinding` / :class:`Help` -- declarative keys and a help view
* :class:`FilePicker` -- filesystem browser
"""

from .filepicker import FileEntry, FilePicker
from .keymap import Help, KeyBinding
from .listview import Item, List
from .paginator import Paginator, PaginatorType
from .progress import Progress
from .spinner import (
    DOTS,
    ELLIPSIS,
    GLOBE,
    HAMBURGER,
    JUMP,
    LINE,
    METER,
    MINI_DOT,
    MONKEY,
    MOON,
    POINTS,
    PULSE,
    Spinner,
    SpinnerStyle,
    SpinnerTickMsg,
)
from .table import Column, Table
from .textinput import EchoMode, TextInput
from .viewport import Viewport

__all__ = [
    "Spinner",
    "SpinnerStyle",
    "SpinnerTickMsg",
    "LINE",
    "DOTS",
    "MINI_DOT",
    "JUMP",
    "PULSE",
    "POINTS",
    "GLOBE",
    "MOON",
    "MONKEY",
    "METER",
    "HAMBURGER",
    "ELLIPSIS",
    "TextInput",
    "EchoMode",
    "Progress",
    "Viewport",
    "List",
    "Item",
    "Table",
    "Column",
    "Paginator",
    "PaginatorType",
    "KeyBinding",
    "Help",
    "FilePicker",
    "FileEntry",
]
