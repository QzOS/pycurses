from lc_screen import lc, lc_check_resize
from lc_term import LC_ATTR_NONE, LC_DIRTY, LC_FORCEPAINT
from lc_window import lc_new


def test_check_resize_noop_when_size_unchanged(monkeypatch):
    win = lc_new(3, 4, 0, 0)
    lc.stdscr = win
    lc.lines = 3
    lc.cols = 4
    lc.screen = []
    lc.hashes = []
    lc.resize_pending = False

    monkeypatch.setattr("lc_screen._get_winsize", lambda: (3, 4))
    assert lc_check_resize() == 0
    assert lc.stdscr is win


def test_check_resize_rebuilds_screen_and_preserves_overlap(monkeypatch):
    win = lc_new(2, 3, 0, 0)
    win.lines[0].line[0].ch = "A"
    win.lines[0].line[1].ch = "B"
    win.lines[1].line[2].ch = "Z"
    win.cury = 1
    win.curx = 2

    lc.stdscr = win
    lc.lines = 2
    lc.cols = 3
    lc.screen = [[None for _ in range(3)] for _ in range(2)]
    lc.hashes = [123, 456]
    lc.resize_pending = True
    lc.cur_y = 9
    lc.cur_x = 9
    lc.cur_attr = 99

    class FakeTerm:
        def __init__(self):
            self.reset_calls = 0

        def reset_state(self):
            self.reset_calls += 1

    fake_term = FakeTerm()
    lc.term = fake_term

    monkeypatch.setattr("lc_screen._get_winsize", lambda: (4, 5))
    assert lc_check_resize() == 1

    assert lc.lines == 4
    assert lc.cols == 5
    assert lc.stdscr is not win
    assert lc.stdscr.lines[0].line[0].ch == "A"
    assert lc.stdscr.lines[0].line[1].ch == "B"
    assert lc.stdscr.lines[1].line[2].ch == "Z"
    assert lc.stdscr.cury == 1
    assert lc.stdscr.curx == 2
    assert len(lc.screen) == 4
    assert len(lc.screen[0]) == 5
    assert lc.hashes == [0, 0, 0, 0]
    assert lc.cur_y == 0
    assert lc.cur_x == 0
    assert lc.cur_attr == LC_ATTR_NONE
    assert fake_term.reset_calls == 1
    assert lc.resize_pending is False

    for row in lc.stdscr.lines:
        assert row.firstch == 0
        assert row.lastch == lc.stdscr.maxx - 1
        assert row.flags == (LC_DIRTY | LC_FORCEPAINT)


def test_check_resize_clamps_cursor_when_new_size_is_smaller(monkeypatch):
    win = lc_new(4, 5, 0, 0)
    win.cury = 3
    win.curx = 4

    lc.stdscr = win
    lc.lines = 4
    lc.cols = 5
    lc.screen = [[None for _ in range(5)] for _ in range(4)]
    lc.hashes = [0, 0, 0, 0]
    lc.resize_pending = True

    class FakeTerm:
        def reset_state(self):
            pass

    lc.term = FakeTerm()

    monkeypatch.setattr("lc_screen._get_winsize", lambda: (2, 3))
    assert lc_check_resize() == 1
    assert lc.stdscr.cury == 1
    assert lc.stdscr.curx == 2


def test_check_resize_ignores_invalid_size(monkeypatch):
    win = lc_new(2, 2, 0, 0)
    lc.stdscr = win
    lc.lines = 2
    lc.cols = 2
    lc.resize_pending = True

    monkeypatch.setattr("lc_screen._get_winsize", lambda: (0, 0))
    assert lc_check_resize() == 0
    assert lc.stdscr is win
    assert lc.resize_pending is False
