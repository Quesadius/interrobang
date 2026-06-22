"""Smoke-test every example so they cannot silently rot.

Each example is imported and, if it defines a model, driven headlessly with a
couple of messages; the print-style demos are simply executed. This guarantees
the examples stay in sync with the library API.
"""

import importlib.util
import io
import os
from contextlib import redirect_stdout

import pytest

from interrobang import KeyMsg, KeyType
from interrobang.testing import drive

EXAMPLES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "examples"))
EXAMPLE_FILES = sorted(
    f for f in os.listdir(EXAMPLES_DIR) if f.endswith(".py") and not f.startswith("_")
)


def load_example(filename):
    path = os.path.join(EXAMPLES_DIR, filename)
    spec = importlib.util.spec_from_file_location(f"example_{filename[:-3]}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def find_model_class(module):
    for value in vars(module).values():
        if (
            isinstance(value, type)
            and value.__module__ == module.__name__
            and hasattr(value, "update")
            and hasattr(value, "view")
        ):
            return value
    return None


@pytest.mark.parametrize("filename", EXAMPLE_FILES)
def test_example_runs(filename):
    module = load_example(filename)
    model_class = find_model_class(module)
    if model_class is not None:
        # Drive the model headlessly with a benign keypress; drive() quits for us.
        output, final = drive(model_class(), [KeyMsg(KeyType.DOWN)])
        assert isinstance(final.view(), str)
    elif hasattr(module, "main"):
        with redirect_stdout(io.StringIO()):
            module.main()
    else:  # pragma: no cover - every example is one of the two shapes above
        pytest.fail(f"{filename} has neither a model nor a main()")


def test_theme_flag_helper():
    from interrobang import CHARM, SOLARIZED_DARK, SOLARIZED_LIGHT, get_theme, set_theme

    shared = load_example("_shared.py")
    try:
        assert shared.apply_theme_flag([]) is None
        assert shared.apply_theme_flag(["--theme", "charm"]) is CHARM
        assert get_theme() is CHARM
        assert shared.apply_theme_flag(["--theme=solarized-light"]) is SOLARIZED_LIGHT
        assert get_theme() is SOLARIZED_LIGHT
        assert shared.wants_fill(["--fill"]) is True
        assert shared.wants_fill([]) is False
    finally:
        set_theme(SOLARIZED_DARK)
