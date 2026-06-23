import time

import pytest

pytest.importorskip("brainflow")

from bci_mcp.core.registry import create_device  # noqa: E402
from bci_mcp.devices.brainflow_device import BrainFlowDevice  # noqa: E402


def test_synthetic_board_roundtrip():
    dev = create_device("brainflow://synthetic")
    assert isinstance(dev, BrainFlowDevice)
    dev.connect()
    dev.start()
    time.sleep(0.5)
    chunk = None
    for _ in range(20):
        chunk = dev.read()
        if chunk is not None and chunk.data.shape[1] > 0:
            break
        time.sleep(0.1)
    dev.stop()
    dev.disconnect()
    assert chunk is not None
    assert chunk.data.shape[0] == dev.info.channel_count
    assert dev.info.channel_count > 0
    assert dev.info.sample_rate > 0
