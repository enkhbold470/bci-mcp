"""Fixed-capacity multi-channel circular buffer over numpy."""
from __future__ import annotations

import numpy as np


class RingBuffer:
    def __init__(self, channels: int, capacity: int) -> None:
        self.channels = channels
        self.capacity = max(1, capacity)
        self._buf = np.zeros((channels, self.capacity), dtype=np.float32)
        self._pos = 0  # next write column
        self._size = 0

    def write(self, data: np.ndarray) -> None:
        n = data.shape[1]
        if n == 0:
            return
        if n >= self.capacity:
            self._buf[:] = data[:, -self.capacity:]
            self._pos = 0
            self._size = self.capacity
            return
        end = self._pos + n
        if end <= self.capacity:
            self._buf[:, self._pos:end] = data
        else:
            first = self.capacity - self._pos
            self._buf[:, self._pos:] = data[:, :first]
            self._buf[:, : n - first] = data[:, first:]
        self._pos = end % self.capacity
        self._size = min(self.capacity, self._size + n)

    def latest(self, n: int) -> np.ndarray:
        n = min(n, self._size)
        if n == 0:
            return np.zeros((self.channels, 0), dtype=np.float32)
        start = (self._pos - n) % self.capacity
        if start + n <= self.capacity:
            return self._buf[:, start : start + n].copy()
        first = self.capacity - start
        return np.concatenate([self._buf[:, start:], self._buf[:, : n - first]], axis=1)

    def __len__(self) -> int:
        return self._size
