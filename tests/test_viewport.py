"""Tests for the Viewport component."""

from interrobang import KeyMsg, KeyType, MouseButton, MouseMsg
from interrobang.components import Viewport
from interrobang.testing import strip_ansi

CONTENT = "\n".join(f"line {i}" for i in range(10))


def make():
    vp = Viewport(width=10, height=3)
    vp.set_content(CONTENT)
    return vp


def test_total_lines():
    assert make().total_lines == 10


def test_initial_at_top():
    vp = make()
    assert vp.at_top
    assert not vp.at_bottom


def test_scroll_down():
    vp = make()
    vp.scroll_down()
    assert vp.y_offset == 1


def test_scroll_clamps_at_bottom():
    vp = make()
    vp.goto_bottom()
    assert vp.y_offset == 7  # 10 lines - 3 visible
    assert vp.at_bottom
    vp.scroll_down(100)
    assert vp.y_offset == 7


def test_scroll_clamps_at_top():
    vp = make()
    vp.scroll_up(100)
    assert vp.y_offset == 0


def test_page_down_up():
    vp = make()
    vp.page_down()
    assert vp.y_offset == 3
    vp.page_up()
    assert vp.y_offset == 0


def test_half_page():
    vp = make()
    vp.half_page_down()
    assert vp.y_offset == 1  # height // 2 == 1


def test_goto_top():
    vp = make()
    vp.goto_bottom()
    vp.goto_top()
    assert vp.y_offset == 0


def test_scroll_percent():
    vp = make()
    assert vp.scroll_percent() == 0.0
    vp.goto_bottom()
    assert vp.scroll_percent() == 1.0


def test_scroll_percent_short_content():
    vp = Viewport(width=10, height=5)
    vp.set_content("a\nb")  # fewer lines than height
    assert vp.scroll_percent() == 1.0


def test_keyboard_scrolling():
    vp = make()
    vp, _ = vp.update(KeyMsg(KeyType.DOWN))
    assert vp.y_offset == 1
    vp, _ = vp.update(KeyMsg(KeyType.UP))
    assert vp.y_offset == 0


def test_vim_keys():
    vp = make()
    vp, _ = vp.update(KeyMsg(KeyType.RUNES, "j"))
    assert vp.y_offset == 1
    vp, _ = vp.update(KeyMsg(KeyType.RUNES, "G"))
    assert vp.at_bottom


def test_mouse_wheel():
    vp = make()
    vp, _ = vp.update(MouseMsg(0, 0, MouseButton.WHEEL_DOWN))
    assert vp.y_offset == 3  # default wheel delta
    vp, _ = vp.update(MouseMsg(0, 0, MouseButton.WHEEL_UP))
    assert vp.y_offset == 0


def test_view_dimensions():
    vp = make()
    lines = strip_ansi(vp.view()).split("\n")
    assert len(lines) == 3
    assert all(len(line) == 10 for line in lines)


def test_view_shows_offset_content():
    vp = make()
    vp.scroll_down(2)
    first_line = strip_ansi(vp.view()).split("\n")[0]
    assert first_line.startswith("line 2")


def test_empty_content():
    vp = Viewport(width=5, height=2)
    lines = strip_ansi(vp.view()).split("\n")
    assert len(lines) == 2
    assert all(line == "     " for line in lines)
