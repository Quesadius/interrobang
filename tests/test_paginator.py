"""Tests for the Paginator component."""

from interrobang import KeyMsg, KeyType
from interrobang.components import Paginator, PaginatorType
from interrobang.testing import strip_ansi


class TestPageMath:
    def test_total_pages(self):
        p = Paginator(per_page=10)
        assert p.set_total_items(95) == 10

    def test_exact_division(self):
        p = Paginator(per_page=10)
        assert p.set_total_items(30) == 3

    def test_zero_items(self):
        p = Paginator(per_page=10)
        assert p.set_total_items(0) == 1

    def test_items_on_first_page(self):
        p = Paginator(per_page=10)
        p.set_total_items(95)
        assert p.items_on_page(95) == 10

    def test_items_on_last_page(self):
        p = Paginator(per_page=10)
        p.set_total_items(95)
        p.page = 9
        assert p.items_on_page(95) == 5

    def test_items_on_page_zero_items(self):
        p = Paginator(per_page=10)
        assert p.items_on_page(0) == 0

    def test_slice_bounds(self):
        p = Paginator(per_page=10)
        p.page = 2
        assert p.slice_bounds() == (20, 30)

    def test_slice_bounds_clamped(self):
        p = Paginator(per_page=10)
        p.set_total_items(25)
        p.page = 2
        assert p.slice_bounds(25) == (20, 25)


class TestNavigation:
    def test_next_prev(self):
        p = Paginator(per_page=10)
        p.set_total_items(95)
        p.next_page()
        assert p.page == 1
        p.prev_page()
        assert p.page == 0

    def test_prev_clamps(self):
        p = Paginator(per_page=10)
        p.set_total_items(95)
        p.prev_page()
        assert p.page == 0

    def test_next_clamps(self):
        p = Paginator(per_page=10)
        p.set_total_items(15)  # 2 pages
        p.next_page()
        p.next_page()
        assert p.page == 1

    def test_on_first_last(self):
        p = Paginator(per_page=10)
        p.set_total_items(15)
        assert p.on_first_page
        p.next_page()
        assert p.on_last_page

    def test_update_keys(self):
        p = Paginator(per_page=10)
        p.set_total_items(95)
        p, _ = p.update(KeyMsg(KeyType.RIGHT))
        assert p.page == 1
        p, _ = p.update(KeyMsg(KeyType.LEFT))
        assert p.page == 0

    def test_set_total_clamps_current_page(self):
        p = Paginator(per_page=10)
        p.set_total_items(95)
        p.page = 9
        p.set_total_items(15)  # now only 2 pages
        assert p.page == 1


class TestView:
    def test_dots(self):
        p = Paginator(per_page=10)
        p.set_total_items(30)
        assert strip_ansi(p.view()) == "● ○ ○"

    def test_dots_active_moves(self):
        p = Paginator(per_page=10)
        p.set_total_items(30)
        p.next_page()
        assert strip_ansi(p.view()) == "○ ● ○"

    def test_arabic(self):
        p = Paginator(per_page=10)
        p.set_total_items(30)
        p.type = PaginatorType.ARABIC
        assert p.view() == "1/3"
