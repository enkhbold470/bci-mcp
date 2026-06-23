"""Device abstraction shared by every EEG backend."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np


@dataclass
class DeviceInfo:
    name: str
    uri: str
    sample_rate: float
    channel_count: int
    channel_names: list[str]
    units: str = "uV"  # "uV" | "counts"
    extra: dict = field(default_factory=dict)


@dataclass
class Chunk:
    data: np.ndarray  # shape (channel_count, n_samples), float32, microvolts
    timestamps: np.ndarray  # shape (n_samples,), seconds


class Device(ABC):
    """A streaming EEG source. Subclasses run their own acquisition internally."""

    info: DeviceInfo

    @abstractmethod
    def connect(self) -> None: ...

    @abstractmethod
    def start(self) -> None: ...

    @abstractmethod
    def read(self) -> Chunk | None:
        """Non-blocking pull of newly available samples, or None if none/not streaming."""

    @abstractmethod
    def stop(self) -> None: ...

    @abstractmethod
    def disconnect(self) -> None: ...

    def __enter__(self) -> Device:
        self.connect()
        self.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self.stop()
        self.disconnect()
