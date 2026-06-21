"""Tests for the MouseMsg helpers."""

from interrobang.mouse import MouseAction, MouseButton, MouseMsg


def test_defaults():
    m = MouseMsg(1, 2)
    assert m.x == 1 and m.y == 2
    assert m.button is MouseButton.NONE
    assert m.action is MouseAction.PRESS


def test_is_wheel_true():
    assert MouseMsg(0, 0, MouseButton.WHEEL_UP).is_wheel
    assert MouseMsg(0, 0, MouseButton.WHEEL_DOWN).is_wheel
    assert MouseMsg(0, 0, MouseButton.WHEEL_LEFT).is_wheel
    assert MouseMsg(0, 0, MouseButton.WHEEL_RIGHT).is_wheel


def test_is_wheel_false():
    assert not MouseMsg(0, 0, MouseButton.LEFT).is_wheel
    assert not MouseMsg(0, 0, MouseButton.NONE).is_wheel


def test_equality():
    assert MouseMsg(1, 2, MouseButton.LEFT) == MouseMsg(1, 2, MouseButton.LEFT)
