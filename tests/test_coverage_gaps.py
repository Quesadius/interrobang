"""Targeted tests filling in less-traveled code paths for full coverage."""

from interrobang import KeyMsg, KeyType
from interrobang._ansi import wrap
from interrobang.command import sequence
from interrobang.components import Column, FilePicker, Item, List, Table, Viewport
from interrobang.style import (
    ANSIColor,
    Color,
    CompleteColor,
    Profile,
)
from interrobang.testing import strip_ansi


# --- _ansi --------------------------------------------------------------


def test_wrap_long_word_after_short_word():
    # The long word is not the first on the line -> hits the mid-line hard break.
    assert wrap("ab cdefghij", 4) == "ab\ncdef\nghij"


# --- command ------------------------------------------------------------


def test_sequence_single_passes_through():
    cmd = lambda: None
    assert sequence(cmd) is cmd


# --- color --------------------------------------------------------------


def test_color_hex_without_hash():
    assert Color("ff0066").sequence(Profile.TRUECOLOR, True, background=False) == "38;2;255;0;102"


def test_color_extended_on_256():
    assert Color(212).sequence(Profile.ANSI256, True, background=False) == "38;5;212"


def test_color_shorthand_on_256():
    assert Color("#f00").sequence(Profile.ANSI256, True, background=False) == "38;5;196"


def test_ansicolor_ascii():
    assert ANSIColor(5).sequence(Profile.ASCII, True, background=False) == ""


def test_complete_color_only_ansi256():
    c = CompleteColor(ansi256=196)
    assert c.sequence(Profile.TRUECOLOR, True, background=False) == "38;5;196"


def test_complete_color_only_ansi():
    c = CompleteColor(ansi=9)
    assert c.sequence(Profile.ANSI, True, background=False) == "91"
    assert c.sequence(Profile.ANSI256, True, background=False) == "38;5;9"


def test_complete_color_ansi256_fallback():
    c = CompleteColor(ansi256=196)
    # No truecolor field, but ANSI profile should degrade the 256 value.
    seq = c.sequence(Profile.ANSI, True, background=False)
    assert seq != ""


# --- viewport key paths -------------------------------------------------


def vp():
    v = Viewport(width=10, height=4)
    v.set_content("\n".join(f"l{i}" for i in range(20)))
    return v


def test_viewport_pgdown_key():
    v = vp()
    v, _ = v.update(KeyMsg(KeyType.PGDOWN))
    assert v.y_offset == 4


def test_viewport_pgup_key():
    v = vp()
    v.goto_bottom()
    v, _ = v.update(KeyMsg(KeyType.PGUP))
    assert v.y_offset == v._max_offset() - 4


def test_viewport_ctrl_keys():
    v = vp()
    v, _ = v.update(KeyMsg(KeyType.RUNES, "d", ctrl=True))
    assert v.y_offset == 2
    v, _ = v.update(KeyMsg(KeyType.RUNES, "u", ctrl=True))
    assert v.y_offset == 0


def test_viewport_g_keys():
    v = vp()
    v, _ = v.update(KeyMsg(KeyType.RUNES, "G"))
    assert v.at_bottom
    v, _ = v.update(KeyMsg(KeyType.RUNES, "g"))
    assert v.at_top


def test_viewport_space_pages():
    v = vp()
    v, _ = v.update(KeyMsg(KeyType.SPACE, " "))
    assert v.y_offset == 4


def test_viewport_visible_line_count():
    v = Viewport(width=5, height=10)
    v.set_content("a\nb\nc")
    assert v.visible_line_count == 3


# --- list paging & status ----------------------------------------------


def long_list():
    items = [Item(f"item {i}", f"desc {i}") for i in range(30)]
    return List(items, width=30, height=8)


def test_list_cursor_down_scrolls_offset():
    lst = long_list()
    for _ in range(10):
        lst, _ = lst.update(KeyMsg(KeyType.DOWN))
    assert lst.offset > 0


def test_list_end_sets_offset():
    lst = long_list()
    lst, _ = lst.update(KeyMsg(KeyType.END))
    assert lst.cursor == 29
    assert lst.offset > 0


def test_list_filter_space():
    lst = long_list()
    lst, _ = lst.update(KeyMsg(KeyType.RUNES, "/"))
    lst, _ = lst.update(KeyMsg(KeyType.RUNES, "item"))
    lst, _ = lst.update(KeyMsg(KeyType.SPACE, " "))
    assert lst.filter_text.endswith(" ")


def test_list_status_bar_filtering():
    lst = long_list()
    lst, _ = lst.update(KeyMsg(KeyType.RUNES, "/"))
    lst, _ = lst.update(KeyMsg(KeyType.RUNES, "5"))
    view = strip_ansi(lst.view())
    assert "/5" in view


def test_list_status_bar_after_filter():
    lst = long_list()
    lst, _ = lst.update(KeyMsg(KeyType.RUNES, "/"))
    lst, _ = lst.update(KeyMsg(KeyType.RUNES, "1"))
    lst, _ = lst.update(KeyMsg(KeyType.ENTER))
    view = strip_ansi(lst.view())
    assert "filter: 1" in view


# --- table --------------------------------------------------------------


def test_table_goto_bottom_scrolls():
    rows = [[f"r{i}", str(i)] for i in range(20)]
    t = Table(columns=[Column("Name", 6), Column("N", 4)], rows=rows, height=6)
    t, _ = t.update(KeyMsg(KeyType.END))
    assert t.cursor == 19
    assert t.offset > 0


# --- filepicker ---------------------------------------------------------


def test_filepicker_missing_dir_returns_empty():
    fp = FilePicker(path="/nonexistent/path/xyz123")
    assert fp.read_dir() == []


def test_filepicker_l_h_keys(tmp_path):
    import os

    os.mkdir(os.path.join(str(tmp_path), "sub"))
    fp = FilePicker(path=str(tmp_path))
    fp, _ = fp.update(KeyMsg(KeyType.RUNES, "l"))  # descend
    assert os.path.basename(fp.current_dir) == "sub"
    fp, _ = fp.update(KeyMsg(KeyType.RUNES, "h"))  # back up
    assert fp.current_dir == os.path.abspath(str(tmp_path))


def test_filepicker_enter_empty_dir(tmp_path):
    fp = FilePicker(path=str(tmp_path))
    fp, _ = fp.update(KeyMsg(KeyType.ENTER))  # nothing to select
    assert fp.did_select_file() is None
