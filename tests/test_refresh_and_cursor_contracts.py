import lc_refresh
import lc_screen
from lc_window import (
    lc_new,
    lc_subwin,
    lc_free,
    lc_wmove,
    lc_wput,
    lc_waddstr,
)


class _DummyTerm:
    def __init__(self) -> None:
        self._last_attr = None

    def move_bytes(self, y: int, x: int) -> bytes:
        return b""

    def attr_bytes(self, attr: int) -> bytes:
        return b""

    def encode_text(self, s: str) -> bytes:
        return s.encode("utf-8", "replace")

    def write_bytes(self, data: bytes | bytearray) -> None:
        pass

    def clear_screen(self) -> None:
        pass

    def reset_state(self) -> None:
        self._last_attr = None

    def note_attr(self, attr: int) -> None:
        self._last_attr = attr


def _install_test_screen(win):
    lc_screen.lc.stdscr = win
    lc_screen.lc.lines = win.maxy
    lc_screen.lc.cols = win.maxx
    lc_screen.lc.screen = [
        [lc_screen.LCCell(" ", 0) for _x in range(win.maxx)]
        for _y in range(win.maxy)
    ]
    lc_screen.lc.hashes = [0 for _ in range(win.maxy)]
    lc_screen.lc.cur_y = 0
    lc_screen.lc.cur_x = 0
    lc_screen.lc.cur_attr = 0
    lc_screen.lc.resize_pending = False
    lc_screen.lc.term = _DummyTerm()


def test_wrefresh_rejects_dead_window(monkeypatch):
    win = lc_new(3, 4, 0, 0)
    assert win is not None
    _install_test_screen(win)

    assert lc_free(win) == 0
    assert win.alive is False

    monkeypatch.setattr(lc_refresh, "lc_check_resize", lambda: 0)

    assert lc_refresh.lc_wrefresh(win) == -1


def test_wput_saturates_cursor_at_last_cell():
    win = lc_new(2, 3, 0, 0)
    assert win is not None

    assert lc_wmove(win, 1, 2) == 0
    assert lc_wput(win, ord("X")) == 0

    assert win.cury == 1
    assert win.curx == 2
    assert win.lines[1].line[2].ch == "X"

    assert lc_wput(win, ord("Y")) == 0
    assert win.cury == 1
    assert win.curx == 2
    assert win.lines[1].line[2].ch == "Y"


def test_waddstr_saturates_cursor_at_last_cell_and_does_not_wrap_to_row_start():
    win = lc_new(2, 3, 0, 0)
    assert win is not None

    assert lc_wmove(win, 1, 2) == 0
    assert lc_waddstr(win, "XY") == 0

    assert win.cury == 1
    assert win.curx == 2
    assert win.lines[1].line[2].ch == "X"
    assert win.lines[1].line[0].ch == " "
    assert win.lines[1].line[1].ch == " "


def test_waddstr_from_penultimate_cell_writes_until_boundary_and_saturates():
    win = lc_new(2, 3, 0, 0)
    assert win is not None

    assert lc_wmove(win, 1, 1) == 0
    assert lc_waddstr(win, "XYZ") == 0

    assert win.lines[1].line[1].ch == "X"
    assert win.lines[1].line[2].ch == "Y"
    assert win.cury == 1
    assert win.curx == 2


def test_wput_and_waddstr_share_same_last_cell_policy():
    a = lc_new(1, 2, 0, 0)
    b = lc_new(1, 2, 0, 0)
    assert a is not None
    assert b is not None

    assert lc_wmove(a, 0, 1) == 0
    assert lc_wmove(b, 0, 1) == 0

    assert lc_wput(a, ord("Q")) == 0
    assert lc_waddstr(b, "Q") == 0

    assert a.cury == b.cury == 0
    assert a.curx == b.curx == 1
    assert a.lines[0].line[1].ch == "Q"
    assert b.lines[0].line[1].ch == "Q"


def test_wrefresh_rejects_stale_subwindow_after_resize(monkeypatch):
    root = lc_new(4, 5, 0, 0)
    assert root is not None

    sub = lc_subwin(root, 2, 2, 1, 1)
    assert sub is not None
    assert sub.alive is True

    _install_test_screen(root)

    replacement = lc_new(6, 7, 0, 0)
    assert replacement is not None

    def _fake_check_resize():
        old = lc_screen.lc.stdscr
        assert old is root
        assert sub.alive is True

        # Simulate the contract effect of a root resize rebuild:
        # all existing derived windows are invalidated, stdscr replaced.
        lc_screen.lc.stdscr = replacement
        lc_screen.lc.lines = replacement.maxy
        lc_screen.lc.cols = replacement.maxx
        lc_screen.lc.screen = [
            [lc_screen.LCCell(" ", 0) for _x in range(replacement.maxx)]
            for _y in range(replacement.maxy)
        ]
        lc_screen.lc.hashes = [0 for _ in range(replacement.maxy)]
        lc_screen.lc.cur_y = 0
        lc_screen.lc.cur_x = 0
        lc_screen.lc.cur_attr = 0
        lc_screen.lc.term = _DummyTerm()

        assert lc_free(sub) == 0
        return 1

    monkeypatch.setattr(lc_refresh, "lc_check_resize", _fake_check_resize)

    assert lc_refresh.lc_wrefresh(sub) == -1
    assert sub.alive is False


def test_wrefresh_root_after_resize_uses_rebuilt_stdscr(monkeypatch):
    root = lc_new(3, 3, 0, 0)
    assert root is not None
    _install_test_screen(root)

    replacement = lc_new(4, 4, 0, 0)
    assert replacement is not None
    replacement.lines[0].line[0].ch = "Z"

    def _fake_check_resize():
        lc_screen.lc.stdscr = replacement
        lc_screen.lc.lines = replacement.maxy
        lc_screen.lc.cols = replacement.maxx
        lc_screen.lc.screen = [
            [lc_screen.LCCell(" ", 0) for _x in range(replacement.maxx)]
            for _y in range(replacement.maxy)
        ]
        lc_screen.lc.hashes = [0 for _ in range(replacement.maxy)]
        lc_screen.lc.cur_y = 0
        lc_screen.lc.cur_x = 0
        lc_screen.lc.cur_attr = 0
        lc_screen.lc.term = _DummyTerm()
        return 1

    monkeypatch.setattr(lc_refresh, "lc_check_resize", _fake_check_resize)

    assert lc_refresh.lc_wrefresh(root) == 0
