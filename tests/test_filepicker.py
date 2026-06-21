"""Tests for the FilePicker component."""

import os

from interrobang import KeyMsg, KeyType
from interrobang.components import FilePicker
from interrobang.testing import strip_ansi


def build_tree(root):
    os.mkdir(os.path.join(root, "alpha"))
    os.mkdir(os.path.join(root, "beta"))
    for name in ("zfile.txt", "afile.txt"):
        with open(os.path.join(root, name), "w") as f:
            f.write("x")
    with open(os.path.join(root, ".hidden"), "w") as f:
        f.write("x")


def press(fp, key_type, runes=""):
    return fp.update(KeyMsg(key_type, runes))[0]


def test_read_dir_sorts_dirs_first(tmp_path):
    build_tree(str(tmp_path))
    fp = FilePicker(path=str(tmp_path))
    names = [e.name for e in fp.read_dir()]
    assert names == ["alpha", "beta", "afile.txt", "zfile.txt"]


def test_hidden_excluded_by_default(tmp_path):
    build_tree(str(tmp_path))
    fp = FilePicker(path=str(tmp_path))
    assert ".hidden" not in [e.name for e in fp.read_dir()]


def test_toggle_hidden(tmp_path):
    build_tree(str(tmp_path))
    fp = FilePicker(path=str(tmp_path))
    fp = press(fp, KeyType.RUNES, ".")
    assert ".hidden" in [e.name for e in fp.read_dir()]


def test_navigation(tmp_path):
    build_tree(str(tmp_path))
    fp = FilePicker(path=str(tmp_path))
    fp = press(fp, KeyType.DOWN)
    assert fp.cursor == 1
    fp = press(fp, KeyType.UP)
    assert fp.cursor == 0


def test_up_clamps(tmp_path):
    build_tree(str(tmp_path))
    fp = FilePicker(path=str(tmp_path))
    fp = press(fp, KeyType.UP)
    assert fp.cursor == 0


def test_descend_into_directory(tmp_path):
    build_tree(str(tmp_path))
    fp = FilePicker(path=str(tmp_path))
    fp = press(fp, KeyType.ENTER)  # cursor 0 -> alpha
    assert os.path.basename(fp.current_dir) == "alpha"
    assert fp.cursor == 0


def test_go_up(tmp_path):
    build_tree(str(tmp_path))
    fp = FilePicker(path=str(tmp_path))
    fp = press(fp, KeyType.ENTER)  # into alpha
    fp = press(fp, KeyType.BACKSPACE)  # back up
    assert fp.current_dir == os.path.abspath(str(tmp_path))


def test_select_file(tmp_path):
    build_tree(str(tmp_path))
    fp = FilePicker(path=str(tmp_path))
    fp = press(fp, KeyType.DOWN)  # beta
    fp = press(fp, KeyType.DOWN)  # afile.txt
    fp = press(fp, KeyType.ENTER)
    chosen = fp.did_select_file()
    assert chosen is not None
    assert os.path.basename(chosen) == "afile.txt"


def test_did_select_file_clears(tmp_path):
    build_tree(str(tmp_path))
    fp = FilePicker(path=str(tmp_path))
    fp = press(fp, KeyType.DOWN)
    fp = press(fp, KeyType.DOWN)
    fp = press(fp, KeyType.ENTER)
    assert fp.did_select_file() is not None
    assert fp.did_select_file() is None  # cleared after read


def test_dir_allowed_selection(tmp_path):
    build_tree(str(tmp_path))
    fp = FilePicker(path=str(tmp_path))
    fp.dir_allowed = True
    fp = press(fp, KeyType.ENTER)  # cursor 0 -> alpha, selected (not descended)
    chosen = fp.did_select_file()
    assert chosen is not None
    assert os.path.basename(chosen) == "alpha"


def test_view_shows_entries(tmp_path):
    build_tree(str(tmp_path))
    fp = FilePicker(path=str(tmp_path))
    view = strip_ansi(fp.view())
    assert "alpha/" in view
    assert "afile.txt" in view


def test_view_empty_dir(tmp_path):
    sub = tmp_path / "empty"
    sub.mkdir()
    fp = FilePicker(path=str(sub))
    assert "empty" in strip_ansi(fp.view())
