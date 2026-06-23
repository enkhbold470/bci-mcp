"""Publish raw EEG and computed metrics to Lab Streaming Layer outlets."""
from __future__ import annotations

import numpy as np


class LSLPublisher:
    def __init__(self, name: str = "BCI-MCP", channel_names: list[str] | None = None,
                 sample_rate: float = 256.0, source_id: str = "bci-mcp-out") -> None:
        self.name = name
        self.channel_names = channel_names or ["ch1"]
        self.sample_rate = sample_rate
        self.source_id = source_id
        self._raw_outlet = None
        self._metrics_outlet = None
        self._metric_keys: list[str] | None = None

    def open(self) -> None:
        from pylsl import StreamInfo, StreamOutlet

        info = StreamInfo(self.name, "EEG", len(self.channel_names),
                          self.sample_rate, "float32", self.source_id)
        self._raw_outlet = StreamOutlet(info)

    def publish_chunk(self, data: np.ndarray) -> None:
        """data: (channels, n_samples) -> pushed as n_samples rows of channels."""
        if self._raw_outlet is None:
            return
        self._raw_outlet.push_chunk(data.T.astype(np.float32).tolist())

    def publish_metrics(self, metrics: dict) -> None:
        from pylsl import StreamInfo, StreamOutlet

        if self._metrics_outlet is None:
            self._metric_keys = sorted(metrics)
            info = StreamInfo(f"{self.name}-metrics", "Markers", len(self._metric_keys),
                              0.0, "float32", f"{self.source_id}-metrics")
            self._metrics_outlet = StreamOutlet(info)
        self._metrics_outlet.push_sample([float(metrics[k]) for k in self._metric_keys])

    def close(self) -> None:
        self._raw_outlet = None
        self._metrics_outlet = None
