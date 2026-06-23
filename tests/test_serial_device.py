import time

import numpy as np

from bci_mcp.devices.serial_device import SerialDevice


class FakeSerial:
    """Minimal stand-in for serial.Serial yielding canned ASCII lines."""

    def __init__(self, lines):
        self._lines = list(lines)
        self.is_open = True
        self.written = []

    @property
    def in_waiting(self):
        return len(self._lines)

    def readline(self):
        return (self._lines.pop(0) + "\n").encode() if self._lines else b""

    def write(self, data):
        self.written.append(data)

    def close(self):
        self.is_open = False


def test_serial_reads_ascii_ints_as_uv():
    fake = FakeSerial(["100", "-50", "garbage", "25"])
    dev = SerialDevice(port="/dev/fake", sample_rate=250.0, scale_uv=1.0,
                       serial_factory=lambda *a, **k: fake)
    dev.connect()
    dev.start()
    time.sleep(0.2)
    chunks = []
    for _ in range(10):
        c = dev.read()
        if c is not None:
            chunks.append(c.data)
        time.sleep(0.02)
    dev.stop()
    dev.disconnect()
    data = np.concatenate(chunks, axis=1) if chunks else np.zeros((1, 0))
    # 3 valid integers parsed (garbage skipped), scaled by scale_uv=1.0
    vals = data[0].tolist()
    assert 100.0 in vals and -50.0 in vals and 25.0 in vals
    assert dev.info.channel_count == 1
    assert dev.info.units == "uV"


def test_start_writes_start_command_when_configured():
    fake = FakeSerial([])
    dev = SerialDevice(port="/dev/fake", start_command=b"b",
                       serial_factory=lambda *a, **k: fake)
    dev.connect()
    dev.start()
    dev.stop()
    dev.disconnect()
    assert b"b" in fake.written
