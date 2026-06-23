import time

import numpy as np
import pytest

from bci_mcp.core.registry import create_device
from bci_mcp.devices.neurofocus import NeuroFocusDevice


class FakeSerial:
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


def test_serial_transport_converts_counts_to_uv():
    fake = FakeSerial(["1000000", "-1000000"])
    dev = NeuroFocusDevice(transport="serial", port="/dev/fake",
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
    data = np.concatenate(chunks, axis=1)
    # 1,000,000 counts × (0.3933/100) µV ≈ 3933 µV
    assert abs(data[0, 0] - 1_000_000 * (3.3 / 8_388_608 * 1e6 / 100.0)) < 1.0
    assert b"b" in fake.written  # start command sent
    assert dev.info.units == "uV"
    assert dev.info.channel_count == 1


def test_registry_parses_serial_and_ble_uris():
    s = create_device("neurofocus://serial//dev/tty.usbmodem1101")
    assert isinstance(s, NeuroFocusDevice)
    assert s.transport == "serial"
    assert s.port.endswith("tty.usbmodem1101")

    b = create_device("neurofocus://ble/NEUROFOCUS_V4_01")
    assert isinstance(b, NeuroFocusDevice)
    assert b.transport == "ble"
    assert b.ble_name == "NEUROFOCUS_V4_01"


def test_ble_transport_requires_bleak_lazily():
    # Constructing a BLE device must NOT require bleak; connecting may.
    dev = NeuroFocusDevice(transport="ble", ble_name="NEUROFOCUS_V4_01")
    assert dev.transport == "ble"


def test_ble_connect_surfaces_not_found(monkeypatch):
    import bleak

    async def _fake_find(name, *args, **kwargs):
        return None

    monkeypatch.setattr(
        bleak.BleakScanner, "find_device_by_name", staticmethod(_fake_find)
    )
    dev = NeuroFocusDevice(transport="ble", ble_name="DOES_NOT_EXIST")
    with pytest.raises(RuntimeError):
        dev.connect()
