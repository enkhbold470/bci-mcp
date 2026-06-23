import numpy as np
import pytest

from bci_mcp.core.device import Chunk, Device, DeviceInfo


def test_device_info_defaults():
    info = DeviceInfo(name="x", uri="synthetic://", sample_rate=256.0,
                      channel_count=2, channel_names=["a", "b"])
    assert info.units == "uV"
    assert info.extra == {}


def test_chunk_holds_array():
    c = Chunk(data=np.zeros((2, 5), dtype=np.float32), timestamps=np.arange(5.0))
    assert c.data.shape == (2, 5)
    assert c.timestamps.shape == (5,)


def test_device_is_abstract():
    with pytest.raises(TypeError):
        Device()  # cannot instantiate ABC with abstract methods
