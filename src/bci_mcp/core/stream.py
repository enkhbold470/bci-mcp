"""Stream: a single producer thread draining a Device into a ring buffer."""
from __future__ import annotations

import threading
import time
from collections.abc import Callable

import numpy as np

from .device import Chunk, Device
from .ringbuffer import RingBuffer


class Stream:
    def __init__(self, device: Device, buffer_seconds: float = 10.0) -> None:
        self.device = device
        capacity = int(device.info.sample_rate * buffer_seconds)
        self.buffer = RingBuffer(device.info.channel_count, capacity)
        self._consumers: list[Callable[[Chunk], None]] = []
        self._thread: threading.Thread | None = None
        self._running = False
        self._lock = threading.Lock()

    def add_consumer(self, callback: Callable[[Chunk], None]) -> None:
        self._consumers.append(callback)

    def start(self) -> None:
        self.device.connect()
        self.device.start()
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        chunk_samples = getattr(self.device, "chunk_samples", None)
        period = (chunk_samples / self.device.info.sample_rate) if chunk_samples else 0.01
        while self._running:
            chunk = self.device.read()
            if chunk is not None and chunk.data.shape[1] > 0:
                with self._lock:
                    self.buffer.write(chunk.data)
                for cb in self._consumers:
                    cb(chunk)
            time.sleep(period)

    def latest(self, n: int) -> np.ndarray:
        with self._lock:
            return self.buffer.latest(n)

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
        self.device.stop()
        self.device.disconnect()
