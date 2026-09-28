"""Run the real Pipeline.current_state() on a hand-built window."""
from __future__ import annotations

import numpy as np

from bci_mcp.devices.synthetic import SyntheticDevice
from bci_mcp.pipeline import Pipeline


def synthetic_window(seed: int, focus: float = 0.5, channels: int = 4,
                     fs: float = 256.0, seconds: float = 2.0) -> np.ndarray:
    dev = SyntheticDevice(channels=channels, sample_rate=fs, focus=focus, seed=seed)
    dev.start()
    # Start at a random phase so windows are not identical up to noise.
    dev._t = int(np.random.default_rng(seed).integers(0, 10_000))
    need = int(fs * seconds)
    chunks = []
    while sum(c.shape[1] for c in chunks) < need:
        chunks.append(dev.read().data)
    return np.concatenate(chunks, axis=1)[:, :need]


def state_for(window: np.ndarray, fs: float, notch: float = 60.0):
    """Push ``window`` through an otherwise-empty Pipeline and return BrainState."""
    channels = window.shape[0]
    dev = SyntheticDevice(channels=channels, sample_rate=fs, seed=0)
    pipe = Pipeline(dev, window_seconds=window.shape[1] / fs, notch_freq=notch)
    pipe.stream.buffer.write(window.astype(np.float32))
    return pipe.current_state()
