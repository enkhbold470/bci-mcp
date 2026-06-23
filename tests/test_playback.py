import time

import numpy as np

from bci_mcp.core.registry import create_device
from bci_mcp.devices.playback import PlaybackDevice
from bci_mcp.pipeline import Pipeline
from bci_mcp.recording.reader import Recording


def test_playback_replays_recording():
    data = np.arange(20, dtype=np.float32).reshape(1, 20)
    rec = Recording(data=data, sample_rate=100.0, channel_names=["ch1"])
    dev = PlaybackDevice(rec, chunk_samples=5)
    dev.connect()
    dev.start()
    collected = []
    for _ in range(20):
        c = dev.read()
        if c is not None:
            collected.append(c.data)
        else:
            break
        time.sleep(0.01)
    dev.stop()
    dev.disconnect()
    out = np.concatenate(collected, axis=1)
    assert np.allclose(out, data)


def test_record_then_playback_via_pipeline(tmp_path):
    path = str(tmp_path / "session.npz")
    p = Pipeline("synthetic://?seed=1")
    p.start()
    time.sleep(0.5)
    out = p.record(seconds=0.5, path=path)
    p.stop()
    assert out == path

    dev = create_device(f"playback://{path}")
    assert isinstance(dev, PlaybackDevice)
    assert dev.info.channel_count == 4
