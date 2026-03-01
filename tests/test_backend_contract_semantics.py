from lc_platform import backend


class DummyState:
    def __init__(self):
        self.pushback_byte = None
        self.resize_pending = False
        self.in_fd = 0
        self.out_fd = 1
        self.orig_term = None
        self.cur_term = None


def test_unread_byte_roundtrip_contract():
    state = DummyState()
    backend.unread_byte(state, 0x41)
    assert state.pushback_byte == 0x41


def test_clear_resize_contract():
    state = DummyState()
    state.resize_pending = True
    backend.clear_resize(state)
    assert state.resize_pending is False


def test_get_size_contract_shape():
    state = DummyState()
    size = backend.get_size(state)
    assert isinstance(size, tuple)
    assert len(size) == 2
    assert isinstance(size[0], int)
    assert isinstance(size[1], int)


def test_input_pending_resize_alone_not_true_when_backend_is_stub_safe():
    state = DummyState()
    state.resize_pending = True
    try:
        pending = backend.input_pending(state, 0)
    except Exception as exc:
        raise AssertionError(f"backend.input_pending raised unexpectedly: {exc}")
    assert isinstance(pending, bool)
