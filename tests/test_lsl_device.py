import time

import pytest

pytest.importorskip("pylsl")

import numpy as np  # noqa: E402
from pylsl import StreamInfo, StreamOutlet  # noqa: E402

from bci_mcp.devices.lsl_device import LSLDevice  # noqa: E402


def test_lsl_roundtrip():
    info = StreamInfo("UnitTestEEG", "EEG", 2, 100.0, "float32", "uid-test-123")
    outlet = StreamOutlet(info)
    time.sleep(0.2)  # let the stream register

    dev = LSLDevice(name="UnitTestEEG")
    dev.connect()
    dev.start()
    time.sleep(0.3)  # allow LSL inlet to fully establish connection
    for _ in range(50):
        outlet.push_sample([1.0, 2.0])
        time.sleep(0.01)

    time.sleep(0.5)  # let data accumulate
    chunk = None
    for _ in range(20):
        chunk = dev.read()
        if chunk is not None and chunk.data.shape[1] > 0:
            break
        time.sleep(0.05)
    dev.stop()
    dev.disconnect()

    assert chunk is not None
    assert chunk.data.shape[0] == 2
    assert dev.info.channel_count == 2
    assert dev.info.sample_rate == 100.0
    assert np.allclose(chunk.data[:, 0], [1.0, 2.0])
