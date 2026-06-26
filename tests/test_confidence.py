"""End-to-end confidence + artifact gating through the live pipeline."""
import time

import numpy as np

from bci_mcp.core.device import Chunk, Device, DeviceInfo
from bci_mcp.pipeline import Pipeline


class FlatlineDevice(Device):
    """Emits zeros — simulates an electrode making no contact."""

    def __init__(self) -> None:
        self.info = DeviceInfo(
            name="Flat", uri="flat://", sample_rate=256.0,
            channel_count=1, channel_names=["ch1"],
        )
        self.chunk_samples = 32
        self._streaming = False

    def connect(self) -> None:
        pass

    def start(self) -> None:
        self._streaming = True

    def stop(self) -> None:
        self._streaming = False

    def disconnect(self) -> None:
        pass

    def read(self) -> Chunk | None:
        if not self._streaming:
            return None
        n = self.chunk_samples
        data = np.zeros((1, n), dtype=np.float32)
        t = np.arange(n, dtype=np.float64) / self.info.sample_rate
        return Chunk(data=data, timestamps=t)


def _wait_state(pipeline, predicate, tries=60):
    state = None
    for _ in range(tries):
        time.sleep(0.1)
        state = pipeline.current_state()
        if state is not None and predicate(state):
            return state
    return state


def test_clean_reading_is_ok_with_confidence():
    p = Pipeline("synthetic://?seed=1", window_seconds=1.0)
    p.start()
    try:
        state = _wait_state(p, lambda s: True)
        assert state is not None
        assert 0.0 < state.confidence <= 1.0
        assert state.status == "ok"
        assert set(state.metric_confidence) == set(state.metrics)
    finally:
        p.stop()


def test_flatline_window_is_unreliable_and_low_confidence():
    p = Pipeline(FlatlineDevice(), window_seconds=1.0)
    p.start()
    try:
        state = _wait_state(p, lambda s: s.status == "unreliable")
        assert state is not None
        assert state.status == "unreliable"
        assert state.confidence <= 0.1
        assert "flatline" in state.artifacts
    finally:
        p.stop()
