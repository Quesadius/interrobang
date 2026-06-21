"""Tests for the frame renderer."""

from interrobang.renderer import Renderer


class FakeWriter:
    def __init__(self):
        self.chunks: list[str] = []
        self.flushes = 0

    def write(self, text):
        self.chunks.append(text)

    def flush(self):
        self.flushes += 1

    @property
    def text(self):
        return "".join(self.chunks)

    def clear(self):
        self.chunks.clear()


class TestInline:
    def test_first_render_writes_content(self):
        w = FakeWriter()
        r = Renderer(w)
        r.render("hello")
        assert "hello" in w.text
        assert w.flushes == 1

    def test_unchanged_frame_skipped(self):
        w = FakeWriter()
        r = Renderer(w)
        r.render("hello")
        w.clear()
        r.render("hello")
        assert w.text == ""

    def test_moves_cursor_up_on_repaint(self):
        w = FakeWriter()
        r = Renderer(w)
        r.render("a\nb\nc")
        w.clear()
        r.render("x\ny\nz")
        # Should move the cursor up 2 lines to repaint a 3-line frame.
        assert "\x1b[2A" in w.text
        assert "x" in w.text and "z" in w.text

    def test_clears_extra_lines_when_shrinking(self):
        w = FakeWriter()
        r = Renderer(w)
        r.render("a\nb\nc")
        w.clear()
        r.render("a")
        # Two trailing lines need clearing.
        assert "\x1b[2K" in w.text

    def test_finish_moves_below(self):
        w = FakeWriter()
        r = Renderer(w)
        r.render("hello")
        w.clear()
        r.finish()
        assert "\r\n" in w.text


class TestAltScreen:
    def test_homes_and_clears(self):
        w = FakeWriter()
        r = Renderer(w, alt_screen=True)
        r.render("a\nb")
        assert "\x1b[H" in w.text
        assert "\x1b[J" in w.text

    def test_alt_screen_property(self):
        r = Renderer(FakeWriter(), alt_screen=True)
        assert r.alt_screen is True


class TestModeSwitch:
    def test_set_alt_screen_forces_repaint(self):
        w = FakeWriter()
        r = Renderer(w)
        r.render("hello")
        r.set_alt_screen(True)
        w.clear()
        r.render("hello")  # same content, but mode changed -> must repaint
        assert "hello" in w.text

    def test_reset_forces_repaint(self):
        w = FakeWriter()
        r = Renderer(w)
        r.render("hello")
        r.reset()
        w.clear()
        r.render("hello")
        assert "hello" in w.text

    def test_finish_noop_in_alt_screen(self):
        w = FakeWriter()
        r = Renderer(w, alt_screen=True)
        r.render("a")
        w.clear()
        r.finish()
        assert w.text == ""
