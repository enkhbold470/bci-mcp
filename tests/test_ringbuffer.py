import numpy as np

from bci_mcp.core.ringbuffer import RingBuffer


def test_partial_fill_then_latest():
    rb = RingBuffer(channels=2, capacity=10)
    rb.write(np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float32))
    assert len(rb) == 3
    out = rb.latest(3)
    assert np.array_equal(out, [[1, 2, 3], [4, 5, 6]])


def test_wraparound_keeps_most_recent():
    rb = RingBuffer(channels=1, capacity=4)
    for i in range(6):
        rb.write(np.array([[i]], dtype=np.float32))
    assert len(rb) == 4
    assert np.array_equal(rb.latest(4), [[2, 3, 4, 5]])


def test_write_larger_than_capacity():
    rb = RingBuffer(channels=1, capacity=3)
    rb.write(np.arange(7, dtype=np.float32).reshape(1, 7))
    assert len(rb) == 3
    assert np.array_equal(rb.latest(3), [[4, 5, 6]])


def test_latest_more_than_available():
    rb = RingBuffer(channels=1, capacity=10)
    rb.write(np.array([[1, 2]], dtype=np.float32))
    assert rb.latest(100).shape == (1, 2)
