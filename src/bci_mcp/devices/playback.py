"""Replay a saved recording as a live Device."""
from __future__ import annotations

import numpy as np

from ..core.device import Chunk, Device, DeviceInfo
from ..core.registry import register
from ..recording.reader import Recording, load_recording


class PlaybackDevice(Device):
    def __init__(self, recording: Recording | str, chunk_samples: int = 32,
                 loop: bool = False, uri: str | None = None) -> None:
        rec = load_recording(recording) if isinstance(recording, str) else recording
        self._rec = rec
        self.chunk_samples = max(1, int(chunk_samples))
        self.loop = loop
        self._pos = 0
        self._streaming = False
        self.info = DeviceInfo(
            name="Playback", uri=uri or "playback://memory",
            sample_rate=rec.sample_rate or 256.0, channel_count=rec.data.shape[0],
            channel_names=rec.channel_names or [f"ch{i + 1}" for i in range(rec.data.shape[0])],
            units="uV", extra={"source": "recording"},
        )

    def connect(self) -> None:
        pass

    def start(self) -> None:
        self._streaming = True
        self._pos = 0

    def read(self) -> Chunk | None:
        if not self._streaming:
            return None
        n_total = self._rec.data.shape[1]
        if self._pos >= n_total:
            if self.loop:
                self._pos = 0
            else:
                return None
        end = min(self._pos + self.chunk_samples, n_total)
        data = self._rec.data[:, self._pos:end].astype(np.float32)
        ts = np.arange(self._pos, end, dtype=np.float64) / self.info.sample_rate
        self._pos = end
        return Chunk(data=data, timestamps=ts)

    def stop(self) -> None:
        self._streaming = False

    def disconnect(self) -> None:
        pass


def _factory(parsed, params):  # noqa: ANN001
    path = (parsed.netloc + parsed.path) or params.get("path", "")
    return PlaybackDevice(
        recording=path,
        loop=params.get("loop", "false").lower() == "true", uri=parsed.geturl(),
    )


register("playback", _factory)
