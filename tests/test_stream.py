import time

from bci_mcp.core.stream import Stream
from bci_mcp.devices.synthetic import SyntheticDevice


def test_stream_fills_buffer():
    dev = SyntheticDevice(channels=2, sample_rate=256.0, chunk_samples=32, seed=1)
    s = Stream(dev, buffer_seconds=2.0)
    s.start()
    time.sleep(0.3)
    s.stop()
    data = s.latest(64)
    assert data.shape[0] == 2
    assert data.shape[1] >= 32


def test_consumer_receives_chunks():
    dev = SyntheticDevice(seed=1)
    s = Stream(dev)
    received = []
    s.add_consumer(lambda chunk: received.append(chunk))
    s.start()
    time.sleep(0.2)
    s.stop()
    assert len(received) > 0
