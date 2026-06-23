"""Generic single-channel serial EEG device (one ASCII integer per line)."""
from __future__ import annotations

import threading
import time

import numpy as np

from ..core.device import Chunk, Device, DeviceInfo
from ..core.registry import register


class SerialDevice(Device):
    def __init__(self, port: str, baud: int = 115200, sample_rate: float = 250.0,
                 scale_uv: float = 1.0, start_command: bytes | None = None,
                 stop_command: bytes | None = None, name: str = "Serial EEG",
                 uri: str | None = None, serial_factory=None) -> None:
        self.info = DeviceInfo(
            name=name, uri=uri or f"serial://{port}", sample_rate=sample_rate,
            channel_count=1, channel_names=["ch1"], units="uV",
        )
        self.port = port
        self.baud = baud
        self.scale_uv = scale_uv
        self.start_command = start_command
        self.stop_command = stop_command
        self._serial_factory = serial_factory
        self._serial = None
        self._buf: list[float] = []
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._running = False

    def _make_serial(self):
        if self._serial_factory is not None:
            return self._serial_factory(self.port, self.baud)
        import serial  # lazy: pyserial is an optional dependency

        return serial.Serial(self.port, self.baud, timeout=1)

    def connect(self) -> None:
        self._serial = self._make_serial()

    def start(self) -> None:
        if self._running:
            return
        if self.start_command:
            self._serial.write(self.start_command)
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while self._running and getattr(self._serial, "is_open", False):
            try:
                if self._serial.in_waiting:
                    line = self._serial.readline().decode("utf-8", errors="ignore").strip()
                    if line:
                        try:
                            value = int(line)
                        except ValueError:
                            continue
                        with self._lock:
                            self._buf.append(value * self.scale_uv)
                else:
                    time.sleep(0.001)
            except (OSError, AttributeError):
                break

    def read(self) -> Chunk | None:
        with self._lock:
            if not self._buf:
                return None
            values = self._buf
            self._buf = []
        data = np.array(values, dtype=np.float32).reshape(1, -1)
        ts = np.arange(data.shape[1], dtype=np.float64) / self.info.sample_rate
        return Chunk(data=data, timestamps=ts)

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
        if self.stop_command and self._serial is not None:
            try:
                self._serial.write(self.stop_command)
            except (OSError, AttributeError):
                pass

    def disconnect(self) -> None:
        if self._serial is not None and getattr(self._serial, "is_open", False):
            self._serial.close()


def _factory(parsed, params):  # noqa: ANN001
    port = (parsed.netloc + parsed.path) or params.get("port", "")
    return SerialDevice(
        port=port,
        baud=int(params.get("baud", 115200)),
        sample_rate=float(params.get("sample_rate", 250.0)),
        scale_uv=float(params.get("scale_uv", 1.0)),
        uri=f"serial://{port}",
    )


register("serial", _factory)
