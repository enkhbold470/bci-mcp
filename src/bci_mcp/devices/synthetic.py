"""Synthetic EEG device — realistic brainwaves with no hardware."""
from __future__ import annotations

import numpy as np

from ..core.device import Chunk, Device, DeviceInfo


class SyntheticDevice(Device):
    """Generates band-mixed EEG. `focus` (0..1) trades alpha for beta."""

    def __init__(
        self,
        channels: int = 4,
        sample_rate: float = 256.0,
        chunk_samples: int = 32,
        focus: float = 0.5,
        seed: int | None = None,
        uri: str = "synthetic://",
    ) -> None:
        self.info = DeviceInfo(
            name="Synthetic EEG",
            uri=uri,
            sample_rate=sample_rate,
            channel_count=channels,
            channel_names=[f"ch{i + 1}" for i in range(channels)],
            units="uV",
        )
        self.chunk_samples = chunk_samples
        self.focus = float(np.clip(focus, 0.0, 1.0))
        self._rng = np.random.default_rng(seed)
        self._t = 0  # sample counter
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
        fs = self.info.sample_rate
        n = self.chunk_samples
        idx = self._t + np.arange(n)
        t = idx / fs
        alpha_amp = 20.0 * (1.0 - self.focus) + 5.0  # 10 Hz
        beta_amp = 18.0 * self.focus + 3.0  # 20 Hz
        base = (
            alpha_amp * np.sin(2 * np.pi * 10 * t)
            + beta_amp * np.sin(2 * np.pi * 20 * t)
            + 8.0 * np.sin(2 * np.pi * 6 * t)  # theta
        )
        data = np.empty((self.info.channel_count, n), dtype=np.float32)
        for c in range(self.info.channel_count):
            noise = self._rng.normal(0.0, 5.0, n)
            data[c] = base + noise
        self._t += n
        return Chunk(data=data, timestamps=t.astype(np.float64))
