"""Tests for parsing raw terminal bytes into key/mouse messages."""

from interrobang._input import parse
from interrobang.key import KeyType
from interrobang.mouse import MouseAction, MouseButton, MouseMsg


def names(data: bytes, flush: bool = False):
    events, remaining = parse(data, flush=flush)
    return [str(e) for e in events], remaining


class TestPrintable:
    def test_single_char(self):
        assert names(b"a") == (["a"], b"")

    def test_multiple_chars(self):
        assert names(b"abc") == (["a", "b", "c"], b"")

    def test_utf8(self):
        assert names("世".encode()) == (["世"], b"")

    def test_partial_utf8_is_held(self):
        events, remaining = parse("世".encode()[:2])
        assert events == []
        assert remaining == "世".encode()[:2]

    def test_invalid_lead_byte_skipped(self):
        events, remaining = parse(b"\xff")
        assert events == []
        assert remaining == b""


class TestControlBytes:
    def test_enter_cr(self):
        assert names(b"\r") == (["enter"], b"")

    def test_enter_lf(self):
        assert names(b"\n") == (["enter"], b"")

    def test_tab(self):
        assert names(b"\t") == (["tab"], b"")

    def test_backspace(self):
        assert names(b"\x7f") == (["backspace"], b"")

    def test_ctrl_c(self):
        assert names(b"\x03") == (["ctrl+c"], b"")

    def test_ctrl_h(self):
        assert names(b"\x08") == (["ctrl+h"], b"")

    def test_ctrl_at(self):
        assert names(b"\x00") == (["ctrl+@"], b"")

    def test_ctrl_backslash(self):
        assert names(b"\x1c") == (["ctrl+\\"], b"")

    def test_space(self):
        assert names(b" ") == (["space"], b"")


class TestEscapeSequences:
    def test_arrows(self):
        assert names(b"\x1b[A") == (["up"], b"")
        assert names(b"\x1b[B") == (["down"], b"")
        assert names(b"\x1b[C") == (["right"], b"")
        assert names(b"\x1b[D") == (["left"], b"")

    def test_home_end(self):
        assert names(b"\x1b[H") == (["home"], b"")
        assert names(b"\x1b[F") == (["end"], b"")

    def test_modified_arrow(self):
        assert names(b"\x1b[1;5C") == (["ctrl+right"], b"")
        assert names(b"\x1b[1;2A") == (["shift+up"], b"")
        assert names(b"\x1b[1;3D") == (["alt+left"], b"")

    def test_tilde_keys(self):
        assert names(b"\x1b[2~") == (["insert"], b"")
        assert names(b"\x1b[3~") == (["delete"], b"")
        assert names(b"\x1b[5~") == (["pgup"], b"")
        assert names(b"\x1b[6~") == (["pgdown"], b"")

    def test_modified_tilde(self):
        assert names(b"\x1b[3;2~") == (["shift+delete"], b"")

    def test_function_keys_tilde(self):
        assert names(b"\x1b[15~") == (["f5"], b"")
        assert names(b"\x1b[24~") == (["f12"], b"")

    def test_function_keys_ss3(self):
        assert names(b"\x1bOP") == (["f1"], b"")
        assert names(b"\x1bOS") == (["f4"], b"")

    def test_ss3_arrow(self):
        assert names(b"\x1bOA") == (["up"], b"")

    def test_shift_tab(self):
        assert names(b"\x1b[Z") == (["shift+tab"], b"")

    def test_alt_char(self):
        assert names(b"\x1ba") == (["alt+a"], b"")

    def test_alt_enter(self):
        assert names(b"\x1b\r") == (["alt+enter"], b"")

    def test_lone_esc_held_without_flush(self):
        events, remaining = parse(b"\x1b")
        assert events == []
        assert remaining == b"\x1b"

    def test_lone_esc_flushed(self):
        assert names(b"\x1b", flush=True) == (["esc"], b"")

    def test_partial_csi_held(self):
        events, remaining = parse(b"\x1b[")
        assert events == []
        assert remaining == b"\x1b["

    def test_unknown_csi_dropped(self):
        # An unrecognized final byte yields no key but is consumed.
        events, remaining = parse(b"\x1b[1;1W")
        assert events == []
        assert remaining == b""


class TestMixedStreams:
    def test_event_then_partial(self):
        events, remaining = parse(b"\x1b[A\x1b[")
        assert [str(e) for e in events] == ["up"]
        assert remaining == b"\x1b["

    def test_text_and_keys(self):
        events, _ = parse(b"hi\x1b[A")
        assert [str(e) for e in events] == ["h", "i", "up"]


class TestEdgeBytes:
    def test_two_byte_utf8(self):
        assert names("é".encode()) == (["é"], b"")

    def test_four_byte_utf8(self):
        assert names("😀".encode()) == (["😀"], b"")

    def test_invalid_continuation_byte(self):
        # 0xc3 promises a continuation byte but '(' is not one.
        events, _ = parse(b"\xc3\x28")
        assert [str(e) for e in events] == ["("]

    def test_private_csi_marker(self):
        # ESC [ ? 2 5 h  -> a private mode sequence; no key, fully consumed.
        events, remaining = parse(b"\x1b[?25h")
        assert events == []
        assert remaining == b""

    def test_unknown_ss3_yields_esc(self):
        events, _ = parse(b"\x1bOZ")
        assert str(events[0]) == "esc"

    def test_esc_esc_flushed(self):
        assert names(b"\x1b\x1b", flush=True) == (["esc", "esc"], b"")

    def test_incomplete_ss3_flushed(self):
        # Flushing emits the dangling ESC, then the 'O' as a literal character.
        assert names(b"\x1bO", flush=True) == (["esc", "O"], b"")


class TestMouse:
    def test_press_left(self):
        events, _ = parse(b"\x1b[<0;10;5M")
        assert events == [MouseMsg(9, 4, MouseButton.LEFT, MouseAction.PRESS)]

    def test_release(self):
        events, _ = parse(b"\x1b[<0;10;5m")
        assert events[0].action is MouseAction.RELEASE

    def test_right_button(self):
        events, _ = parse(b"\x1b[<2;1;1M")
        assert events[0].button is MouseButton.RIGHT

    def test_wheel_up(self):
        events, _ = parse(b"\x1b[<64;3;3M")
        assert events[0].button is MouseButton.WHEEL_UP

    def test_wheel_down(self):
        events, _ = parse(b"\x1b[<65;3;3M")
        assert events[0].button is MouseButton.WHEEL_DOWN

    def test_motion(self):
        events, _ = parse(b"\x1b[<32;5;5M")
        assert events[0].action is MouseAction.MOTION

    def test_modifiers(self):
        events, _ = parse(b"\x1b[<4;1;1M")
        assert events[0].shift is True

    def test_malformed_mouse_dropped(self):
        events, remaining = parse(b"\x1b[<0;10M")
        assert events == []
        assert remaining == b""
