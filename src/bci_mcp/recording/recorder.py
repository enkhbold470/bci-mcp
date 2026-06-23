"""A Stream consumer that accumulates chunks for later saving."""
from __future__ import annotations

import numpy as np

from ..core.device import Chunk


class Recorder:
    def __init__(self) -> None:
        self._chunks: list[np.ndarray] = []
        self._active = False

    def start(self) -> None:
        self._active = True

    def stop(self) -> None:
        self._active = False

    def __call__(self, chunk: Chunk) -> None:
        if self._active:
            self._chunks.append(chunk.data.copy())

    def data(self) -> np.ndarray:
        if not self._chunks:
            return np.zeros((0, 0), dtype=np.float32)
        return np.concatenate(self._chunks, axis=1)
