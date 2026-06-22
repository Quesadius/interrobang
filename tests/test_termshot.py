"""Tests for the ANSI->SVG screenshot renderer in tools/termshot.py.

Guards the documentation-image pipeline: the converter must keep turning real
component output into valid, faithful SVG.
"""

import importlib.util
import os
import xml.etree.ElementTree as ET

from interrobang.style import Color, Style

_PATH = os.path.join(os.path.dirname(__file__), "..", "tools", "termshot.py")
_spec = importlib.util.spec_from_file_location("termshot", _PATH)
termshot = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(termshot)


def test_render_svg_is_valid_xml():
    svg = termshot.render_svg(Style().bold().render("hello"), "demo")
    ET.fromstring(svg)  # raises if malformed
    assert svg.startswith("<svg")
    assert "hello" in svg


def test_truecolor_foreground_preserved():
    svg = termshot.render_svg(Style().foreground(Color("#ff0066")).render("x"))
    assert "#ff0066" in svg


def test_attributes_render():
    svg = termshot.render_svg(Style().bold().italic().underline().render("x"))
    assert 'font-weight="bold"' in svg
    assert 'font-style="italic"' in svg
    assert "underline" in svg


def test_background_draws_rect():
    svg = termshot.render_svg(Style().background(Color("#7d56f4")).padding(0, 1).render("x"))
    assert "<rect" in svg
    assert "#7d56f4" in svg


def test_ansi256_color_maps_to_rgb():
    # Color(212) renders as 38;5;212; the converter must resolve it to a hex fill.
    svg = termshot.render_svg(Style().foreground(Color(212)).render("x"))
    ET.fromstring(svg)
    assert "fill=\"#" in svg


def test_xml_escaping():
    svg = termshot.render_svg("a < b & c > d")
    ET.fromstring(svg)
    assert "&lt;" in svg and "&amp;" in svg and "&gt;" in svg


def test_wide_characters_supported():
    svg = termshot.render_svg("世界 hello")
    ET.fromstring(svg)
    assert "世界" in svg


def test_animated_svg_cycles_frames():
    svg = termshot.render_animated_svg(["a", "b", "c"], "anim", fps=3)
    ET.fromstring(svg)
    assert svg.count("<animate") == 3
    assert 'repeatCount="indefinite"' in svg


def test_animated_first_frame_visible():
    svg = termshot.render_animated_svg(["one", "two"], fps=2)
    # The first frame group starts visible so non-animating viewers see something.
    assert 'opacity="1"' in svg
