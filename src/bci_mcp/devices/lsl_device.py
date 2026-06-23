"""Lab Streaming Layer (LSL) inlet device — consume any LSL EEG stream."""
from __future__ import annotations

import numpy as np

from ..core.device import Chunk, Device, DeviceInfo
from ..core.registry import register


class LSLDevice(Device):
    def __init__(self, name: str = "", stream_type: str = "EEG",
                 resolve_timeout: float = 5.0, uri: str | None = None) -> None:
        self.name = name
        self.stream_type = stream_type
        self.resolve_timeout = resolve_timeout
        self._inlet = None
        # info is filled in connect() once the stream is resolved
        self.info = DeviceInfo(
            name=f"LSL:{name or stream_type}", uri=uri or f"lsl://{name}",
            sample_rate=0.0, channel_count=0, channel_names=[], units="uV",
        )

    def connect(self) -> None:
        from pylsl import StreamInlet, resolve_byprop

        prop, value = ("name", self.name) if self.name else ("type", self.stream_type)
        streams = resolve_byprop(prop, value, timeout=self.resolve_timeout)
        if not streams:
            raise RuntimeError(f"No LSL stream found for {prop}={value!r}")
        self._inlet = StreamInlet(streams[0], max_buflen=60)
        self._inlet.open_stream()
        si = self._inlet.info()
        self.info = DeviceInfo(
            name=f"LSL:{si.name()}", uri=self.info.uri,
            sample_rate=float(si.nominal_srate()), channel_count=si.channel_count(),
            channel_names=[f"ch{i + 1}" for i in range(si.channel_count())],
            units="uV", extra={"source_id": si.source_id()},
        )

    def start(self) -> None:
        pass  # inlet pulls on demand

    def read(self) -> Chunk | None:
        samples, timestamps = self._inlet.pull_chunk(timeout=0.0)
        if not samples:
            return None
        data = np.asarray(samples, dtype=np.float32).T  # (channels, n)
        ts = np.asarray(timestamps, dtype=np.float64)
        return Chunk(data=data, timestamps=ts)

    def stop(self) -> None:
        pass

    def disconnect(self) -> None:
        if self._inlet is not None:
            self._inlet.close_stream()


def _factory(parsed, params):  # noqa: ANN001
    name = parsed.netloc or params.get("name", "")
    return LSLDevice(name=name, stream_type=params.get("type", "EEG"),
                     uri=parsed.geturl())


register("lsl", _factory)
