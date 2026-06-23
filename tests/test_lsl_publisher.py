import time

import pytest

pytest.importorskip("pylsl")

import numpy as np  # noqa: E402

from bci_mcp.lsl.publisher import LSLPublisher  # noqa: E402


def test_raw_publish_roundtrip():
    from pylsl import StreamInlet, resolve_byprop

    pub = LSLPublisher(name="BCITestOut", channel_names=["a", "b"], sample_rate=100.0)
    pub.open()
    time.sleep(0.2)
    streams = resolve_byprop("name", "BCITestOut", timeout=5.0)
    assert streams, "publisher stream not found"
    inlet = StreamInlet(streams[0])
    inlet.open_stream()
    for _ in range(20):
        pub.publish_chunk(np.array([[1.0], [2.0]], dtype=np.float32))
        time.sleep(0.005)
    sample = None
    for _ in range(20):
        sample, _ = inlet.pull_sample(timeout=0.0)
        if sample is not None:
            break
        time.sleep(0.05)
    inlet.close_stream()
    pub.close()
    assert sample is not None
    assert np.allclose(sample, [1.0, 2.0])
