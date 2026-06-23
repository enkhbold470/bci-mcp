# BCI-MCP Plan 2 — Hardware device backends

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development / executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Make "any EEG device" real: add NeuroFocus v4 (serial + BLE), a generic single-channel serial device, BrainFlow (OpenBCI/Muse/…), and LSL backends — all behind the existing `Device`/registry interface, validated with byte-level fixtures and in-process round-trips (no physical hardware).

**Architecture:** Each backend is a `Device` subclass that runs its own acquisition (reader thread or async loop) and exposes `read()` returning a `Chunk` of µV samples, identical to `SyntheticDevice`. A pure, unit-tested NeuroFocus protocol module decodes both ASCII and binary-batch frames so the transport code stays thin. Library wrappers (bleak/brainflow/pylsl) are verified against the installed API and adapted if needed.

**Tech stack:** pyserial, bleak, brainflow, pylsl (the `[devices]` + `[lsl]` extras). numpy.

**Builds on Plan 1.** The package already has `core.device` (`Device`, `Chunk`, `DeviceInfo`), `core.registry` (`create_device`, `register`), `core.stream`, `pipeline.Pipeline`, and `devices.synthetic`. Install dev+device deps first: `python3 -m pip install -e ".[dev,devices,lsl]"`.

**Conventions:** source under `src/bci_mcp/`, tests under `tests/`, `python3 -m pytest`, `ruff check src tests`, commit per task. Tests that need an optional lib use `pytest.importorskip("<lib>")`.

---

### Task 1: NeuroFocus protocol (pure, fully testable)

**Files:**
- Create: `src/bci_mcp/devices/neurofocus_protocol.py`
- Create: `tests/test_neurofocus_protocol.py`

Source of truth (from the NeuroFocus v4 firmware docs): single channel; raw signed 24-bit ADC counts; ADC LSB = 3.3 V / 2²³ ≈ 0.3933 µV/count at the ADC; an AD8422 instrumentation amp with gain 100 sits before the ADC, so scalp-referred µV = counts × LSB ÷ 100. Default sample rate ≈ 600 SPS. BLE service `0338ff7c-6251-4029-a5d5-24e4fa856c8d`, data char (notify) `ad615f2b-cc93-4155-9e4d-f5f32cb9a2d7`, command char (write) `b5e3d1c9-8a2f-4e7b-9c6d-1a3f5e7b9c2d`. ASCII mode = one decimal integer string per notification. Binary-batch mode = `0xE7 0x1E` magic, `seq` uint16-LE, `n` uint8, then `n` × int32-LE counts. Commands: `b`=start, `s`=stop, `v`=reset.

- [ ] **Step 1: Write the failing test**

Create `tests/test_neurofocus_protocol.py`:

```python
import struct

import numpy as np
import pytest

from bci_mcp.devices import neurofocus_protocol as nf


def test_counts_to_uv_scalp_referred():
    # 1 count → LSB/gain microvolts; ~0.003933 µV
    assert nf.counts_to_uv(1) == pytest.approx(3.3 / 8_388_608 * 1e6 / 100.0, rel=1e-6)
    assert nf.counts_to_uv(0) == 0.0


def test_parse_ascii_frame():
    assert nf.parse_frame(b"12345") == [12345]
    assert nf.parse_frame(b"-678\n") == [-678]


def test_parse_ascii_ignores_blank():
    assert nf.parse_frame(b"   ") == []


def test_parse_binary_batch_frame():
    samples = [1, -2, 3, 4, -5, 6, 7, -8]
    payload = b"\xe7\x1e" + struct.pack("<H", 42) + struct.pack("<B", len(samples))
    payload += b"".join(struct.pack("<i", s) for s in samples)
    assert nf.parse_frame(payload) == samples


def test_uuids_present():
    assert nf.SERVICE_UUID == "0338ff7c-6251-4029-a5d5-24e4fa856c8d"
    assert nf.DATA_CHAR_UUID == "ad615f2b-cc93-4155-9e4d-f5f32cb9a2d7"
    assert nf.CMD_CHAR_UUID == "b5e3d1c9-8a2f-4e7b-9c6d-1a3f5e7b9c2d"


def test_counts_array_to_uv_chunk():
    counts = np.array([0, 1000, -1000], dtype=np.int64)
    uv = nf.counts_to_uv(counts)
    assert uv.shape == (3,)
    assert uv[0] == 0.0
```

- [ ] **Step 2: Run test, confirm it fails** — `python3 -m pytest tests/test_neurofocus_protocol.py -v` → ModuleNotFoundError.

- [ ] **Step 3: Implement**

Create `src/bci_mcp/devices/neurofocus_protocol.py`:

```python
"""NeuroFocus v4 wire protocol — pure decode helpers (no I/O)."""
from __future__ import annotations

import struct

import numpy as np

SERVICE_UUID = "0338ff7c-6251-4029-a5d5-24e4fa856c8d"
DATA_CHAR_UUID = "ad615f2b-cc93-4155-9e4d-f5f32cb9a2d7"
CMD_CHAR_UUID = "b5e3d1c9-8a2f-4e7b-9c6d-1a3f5e7b9c2d"

CMD_START = b"b"
CMD_STOP = b"s"
CMD_RESET = b"v"

DEFAULT_SAMPLE_RATE = 600.0
ADC_LSB_UV = 3.3 / 8_388_608 * 1e6  # ≈0.3933 µV/count at the ADC input
AMP_GAIN = 100.0  # AD8422 instrumentation amplifier
_BINARY_MAGIC = b"\xe7\x1e"


def counts_to_uv(counts):
    """Convert raw 24-bit ADC counts to scalp-referred microvolts."""
    return np.asarray(counts) * (ADC_LSB_UV / AMP_GAIN) if np.ndim(counts) else (
        counts * (ADC_LSB_UV / AMP_GAIN)
    )


def parse_frame(payload: bytes) -> list[int]:
    """Decode one BLE/serial payload into a list of raw ADC counts.

    Supports binary-batch frames (0xE7 0x1E magic) and ASCII decimal frames.
    Returns [] for blank/unparseable ASCII.
    """
    if payload[:2] == _BINARY_MAGIC:
        n = payload[4]
        offset = 5
        out: list[int] = []
        for i in range(n):
            (value,) = struct.unpack_from("<i", payload, offset + i * 4)
            out.append(value)
        return out
    text = payload.decode("utf-8", errors="ignore").strip()
    if not text:
        return []
    try:
        return [int(text)]
    except ValueError:
        return []
```

- [ ] **Step 4: Run test, confirm pass** — `python3 -m pytest tests/test_neurofocus_protocol.py -v` → 6 passed.

- [ ] **Step 5: Commit** — `git add src/bci_mcp/devices/neurofocus_protocol.py tests/test_neurofocus_protocol.py && git commit -m "feat: NeuroFocus v4 wire protocol decode (ASCII + binary batch)"`

---

### Task 2: Generic serial device (`serial://`)

**Files:**
- Create: `src/bci_mcp/devices/serial_device.py`
- Modify: `src/bci_mcp/devices/__init__.py` (import to register)
- Create: `tests/test_serial_device.py`

A generic single-channel device that reads one ASCII integer per line from a serial port. Testable by injecting a fake serial object (no hardware). `pyserial` is only imported lazily so the package still imports without it.

- [ ] **Step 1: Write the failing test**

Create `tests/test_serial_device.py`:

```python
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
```

- [ ] **Step 2: Run test, confirm fail** — ModuleNotFoundError.

- [ ] **Step 3: Implement**

Create `src/bci_mcp/devices/serial_device.py`:

```python
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
```

- [ ] **Step 4: Register on import** — add to `src/bci_mcp/devices/__init__.py`:

```python
from . import serial_device as _serial_device  # noqa: F401
```

- [ ] **Step 5: Run test, confirm pass** — `python3 -m pytest tests/test_serial_device.py -v` → 2 passed.

- [ ] **Step 6: Commit** — `git add src/bci_mcp/devices/serial_device.py src/bci_mcp/devices/__init__.py tests/test_serial_device.py && git commit -m "feat: generic serial EEG device (serial://)"`

---

### Task 3: NeuroFocus device (serial + BLE)

**Files:**
- Create: `src/bci_mcp/devices/neurofocus.py`
- Modify: `src/bci_mcp/devices/__init__.py`
- Create: `tests/test_neurofocus_device.py`

`NeuroFocusDevice` has two transports selected by URI: `neurofocus://serial/<port>` and `neurofocus://ble/<name>`. Both convert raw counts to µV via the protocol module and emit identical `Chunk`s. The serial transport is testable with a fake serial; the BLE transport's decoding is already covered by the protocol tests, and its URI parsing is tested here. `bleak` is imported lazily inside the BLE code path.

- [ ] **Step 1: Write the failing test**

Create `tests/test_neurofocus_device.py`:

```python
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
```

- [ ] **Step 2: Run test, confirm fail** — ModuleNotFoundError.

- [ ] **Step 3: Implement**

Create `src/bci_mcp/devices/neurofocus.py`. The serial transport mirrors `SerialDevice` but routes bytes through `neurofocus_protocol`. The BLE transport runs an asyncio loop in a background thread using `bleak.BleakClient`, subscribes to the data characteristic, decodes each notification with `parse_frame`, and pushes µV samples into a shared buffer. **Verify the installed `bleak` API** (`python3 -c "import bleak, inspect; print(bleak.__version__)"`) and adapt the client/notify calls if the installed version differs (e.g. `start_notify(uuid, cb)` callback signature `(sender, data)`; `BleakScanner.find_device_by_name`). Keep the decode path identical to the serial transport.

```python
"""NeuroFocus v4 device — USB-serial and BLE transports."""
from __future__ import annotations

import threading
import time

import numpy as np

from ..core.device import Chunk, Device, DeviceInfo
from ..core.registry import register
from . import neurofocus_protocol as proto


class NeuroFocusDevice(Device):
    def __init__(self, transport: str = "serial", port: str = "",
                 ble_name: str = "NEUROFOCUS_V4_01",
                 sample_rate: float = proto.DEFAULT_SAMPLE_RATE,
                 baud: int = 115200, uri: str | None = None,
                 serial_factory=None) -> None:
        self.transport = transport
        self.port = port
        self.ble_name = ble_name
        self.baud = baud
        self._serial_factory = serial_factory
        self.info = DeviceInfo(
            name=f"NeuroFocus v4 ({transport})",
            uri=uri or (f"neurofocus://serial/{port}" if transport == "serial"
                        else f"neurofocus://ble/{ble_name}"),
            sample_rate=sample_rate, channel_count=1, channel_names=["ch1"],
            units="uV", extra={"transport": transport},
        )
        self._buf: list[float] = []
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._running = False
        self._serial = None
        self._ble_client = None
        self._loop = None

    # --- shared ---
    def _emit_counts(self, counts) -> None:
        if not counts:
            return
        uv = proto.counts_to_uv(np.asarray(counts, dtype=np.int64))
        with self._lock:
            self._buf.extend(float(x) for x in np.atleast_1d(uv))

    def read(self) -> Chunk | None:
        with self._lock:
            if not self._buf:
                return None
            values = self._buf
            self._buf = []
        data = np.array(values, dtype=np.float32).reshape(1, -1)
        ts = np.arange(data.shape[1], dtype=np.float64) / self.info.sample_rate
        return Chunk(data=data, timestamps=ts)

    # --- lifecycle dispatch ---
    def connect(self) -> None:
        if self.transport == "serial":
            self._connect_serial()
        else:
            self._connect_ble()

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        if self.transport == "serial":
            self._serial.write(proto.CMD_START)
            self._thread = threading.Thread(target=self._run_serial, daemon=True)
            self._thread.start()
        # BLE auto-streams on connect; notifications already flowing.

    def stop(self) -> None:
        self._running = False
        if self.transport == "serial" and self._serial is not None:
            try:
                self._serial.write(proto.CMD_STOP)
            except (OSError, AttributeError):
                pass
            if self._thread is not None:
                self._thread.join(timeout=1.0)

    def disconnect(self) -> None:
        if self.transport == "serial":
            if self._serial is not None and getattr(self._serial, "is_open", False):
                self._serial.close()
        else:
            self._disconnect_ble()

    # --- serial transport ---
    def _connect_serial(self) -> None:
        if self._serial_factory is not None:
            self._serial = self._serial_factory(self.port, self.baud)
        else:
            import serial
            self._serial = serial.Serial(self.port, self.baud, timeout=1)

    def _run_serial(self) -> None:
        while self._running and getattr(self._serial, "is_open", False):
            try:
                if self._serial.in_waiting:
                    line = self._serial.readline()
                    self._emit_counts(proto.parse_frame(line))
                else:
                    time.sleep(0.001)
            except (OSError, AttributeError):
                break

    # --- BLE transport (verify/adapt against installed bleak) ---
    def _connect_ble(self) -> None:
        import asyncio

        import bleak

        self._loop = asyncio.new_event_loop()

        def _notify(_sender, data: bytearray) -> None:
            self._emit_counts(proto.parse_frame(bytes(data)))

        async def _setup() -> None:
            device = await bleak.BleakScanner.find_device_by_name(self.ble_name)
            if device is None:
                raise RuntimeError(f"NeuroFocus BLE device '{self.ble_name}' not found")
            self._ble_client = bleak.BleakClient(device)
            await self._ble_client.connect()
            await self._ble_client.start_notify(proto.DATA_CHAR_UUID, _notify)
            await self._ble_client.write_gatt_char(proto.CMD_CHAR_UUID, proto.CMD_START)

        def _run_loop() -> None:
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(_setup())
            self._loop.run_forever()

        self._running = True
        self._thread = threading.Thread(target=_run_loop, daemon=True)
        self._thread.start()
        time.sleep(0.1)  # give the loop a moment to start connecting

    def _disconnect_ble(self) -> None:
        self._running = False
        if self._loop is not None and self._ble_client is not None:
            import asyncio

            async def _teardown() -> None:
                try:
                    await self._ble_client.stop_notify(proto.DATA_CHAR_UUID)
                except Exception:
                    pass
                await self._ble_client.disconnect()

            try:
                fut = asyncio.run_coroutine_threadsafe(_teardown(), self._loop)
                fut.result(timeout=2.0)
            except Exception:
                pass
            self._loop.call_soon_threadsafe(self._loop.stop)


def _factory(parsed, params):  # noqa: ANN001
    # neurofocus://serial/<port>  or  neurofocus://ble/<name>
    transport = parsed.netloc or "serial"
    rest = parsed.path.lstrip("/")
    if transport == "serial":
        return NeuroFocusDevice(transport="serial", port="/" + rest if rest else "",
                                uri=parsed.geturl())
    return NeuroFocusDevice(transport="ble", ble_name=rest or "NEUROFOCUS_V4_01",
                            uri=parsed.geturl())


register("neurofocus", _factory)
```

Note on the serial-URI port: `neurofocus://serial//dev/tty.usbmodem1101` parses with `netloc="serial"` and `path="/dev/tty.usbmodem1101"`; the factory strips the leading slash group and re-prepends one so `port` is `/dev/tty.usbmodem1101`. Confirm the test's `port.endswith(...)` passes; adjust the slash handling if your urlparse yields a different split, keeping the test green.

- [ ] **Step 4: Register on import** — add to `src/bci_mcp/devices/__init__.py`:

```python
from . import neurofocus as _neurofocus  # noqa: F401
```

- [ ] **Step 5: Run test, confirm pass** — `python3 -m pytest tests/test_neurofocus_device.py -v` → 3 passed. (The BLE path is not exercised live; only construction + URI parsing.)

- [ ] **Step 6: Commit** — `git add src/bci_mcp/devices/neurofocus.py src/bci_mcp/devices/__init__.py tests/test_neurofocus_device.py && git commit -m "feat: NeuroFocus v4 device (serial + BLE transports)"`

---

### Task 4: BrainFlow device (OpenBCI / Muse / many boards)

**Files:**
- Create: `src/bci_mcp/devices/brainflow_device.py`
- Modify: `src/bci_mcp/devices/__init__.py`
- Create: `tests/test_brainflow_device.py`

Wrap BrainFlow behind `Device`. URI: `brainflow://<board>?serial_port=...&mac_address=...`. Map friendly board names → `BoardIds`. The BrainFlow **synthetic board** needs no hardware, so the test does a real round-trip against it. Import `brainflow` lazily; the test uses `pytest.importorskip("brainflow")`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_brainflow_device.py`:

```python
import time

import pytest

pytest.importorskip("brainflow")

from bci_mcp.core.registry import create_device  # noqa: E402
from bci_mcp.devices.brainflow_device import BrainFlowDevice  # noqa: E402


def test_synthetic_board_roundtrip():
    dev = create_device("brainflow://synthetic")
    assert isinstance(dev, BrainFlowDevice)
    dev.connect()
    dev.start()
    time.sleep(0.5)
    chunk = None
    for _ in range(20):
        chunk = dev.read()
        if chunk is not None and chunk.data.shape[1] > 0:
            break
        time.sleep(0.1)
    dev.stop()
    dev.disconnect()
    assert chunk is not None
    assert chunk.data.shape[0] == dev.info.channel_count
    assert dev.info.channel_count > 0
    assert dev.info.sample_rate > 0
```

- [ ] **Step 2: Run test, confirm fail** — ModuleNotFoundError (or skip if brainflow missing; install it: `python3 -m pip install -e ".[devices]"`).

- [ ] **Step 3: Implement**

Create `src/bci_mcp/devices/brainflow_device.py`. **Verify the installed BrainFlow API** (`from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds`) and the channel/rate helper names (`BoardShim.get_eeg_channels`, `get_sampling_rate`, `get_board_data`) before finalizing; adapt if the installed version differs.

```python
"""BrainFlow-backed device: OpenBCI, Muse, Neurosity, synthetic, and more."""
from __future__ import annotations

import numpy as np

from ..core.device import Chunk, Device, DeviceInfo
from ..core.registry import register

_BOARD_ALIASES = {
    "synthetic": "SYNTHETIC_BOARD",
    "cyton": "CYTON_BOARD",
    "ganglion": "GANGLION_BOARD",
    "cyton_daisy": "CYTON_DAISY_BOARD",
    "muse_2": "MUSE_2_BOARD",
    "muse_s": "MUSE_S_BOARD",
    "muse_2016": "MUSE_2016_BOARD",
}


class BrainFlowDevice(Device):
    def __init__(self, board: str = "synthetic", serial_port: str = "",
                 mac_address: str = "", uri: str | None = None) -> None:
        from brainflow.board_shim import BoardIds, BoardShim, BrainFlowInputParams

        board_key = _BOARD_ALIASES.get(board, board.upper())
        self._board_id = int(getattr(BoardIds, board_key).value)
        params = BrainFlowInputParams()
        if serial_port:
            params.serial_port = serial_port
        if mac_address:
            params.mac_address = mac_address
        self._shim = BoardShim(self._board_id, params)
        self._eeg_channels = BoardShim.get_eeg_channels(self._board_id)
        sample_rate = float(BoardShim.get_sampling_rate(self._board_id))
        self.info = DeviceInfo(
            name=f"BrainFlow:{board}", uri=uri or f"brainflow://{board}",
            sample_rate=sample_rate, channel_count=len(self._eeg_channels),
            channel_names=[f"ch{i + 1}" for i in range(len(self._eeg_channels))],
            units="uV", extra={"board_id": self._board_id},
        )

    def connect(self) -> None:
        self._shim.prepare_session()

    def start(self) -> None:
        self._shim.start_stream()

    def read(self) -> Chunk | None:
        raw = self._shim.get_board_data()  # (rows, n_samples); empties the ring buffer
        if raw.shape[1] == 0:
            return None
        data = raw[self._eeg_channels, :].astype(np.float32)
        ts = np.arange(data.shape[1], dtype=np.float64) / self.info.sample_rate
        return Chunk(data=data, timestamps=ts)

    def stop(self) -> None:
        if self._shim.is_prepared():
            self._shim.stop_stream()

    def disconnect(self) -> None:
        if self._shim.is_prepared():
            self._shim.release_session()


def _factory(parsed, params):  # noqa: ANN001
    board = parsed.netloc or params.get("board", "synthetic")
    return BrainFlowDevice(
        board=board, serial_port=params.get("serial_port", ""),
        mac_address=params.get("mac_address", ""), uri=parsed.geturl(),
    )


register("brainflow", _factory)
```

- [ ] **Step 4: Register on import** — add to `src/bci_mcp/devices/__init__.py` with a guard so a missing brainflow dep doesn't break package import:

```python
try:  # brainflow is an optional dependency
    from . import brainflow_device as _brainflow_device  # noqa: F401
except Exception:  # pragma: no cover
    pass
```

Note: registration happens at import of `brainflow_device`, but that module only imports brainflow inside `BrainFlowDevice.__init__`, so the `try/except` only guards genuinely broken environments. Confirm `create_device("brainflow://synthetic")` still works when brainflow is installed.

- [ ] **Step 5: Run test, confirm pass** (with brainflow installed) — `python3 -m pip install -e ".[devices]" && python3 -m pytest tests/test_brainflow_device.py -v` → 1 passed.

- [ ] **Step 6: Commit** — `git add src/bci_mcp/devices/brainflow_device.py src/bci_mcp/devices/__init__.py tests/test_brainflow_device.py && git commit -m "feat: BrainFlow device (OpenBCI/Muse/synthetic via BrainFlow)"`

---

### Task 5: LSL device (consume any Lab Streaming Layer stream)

**Files:**
- Create: `src/bci_mcp/devices/lsl_device.py`
- Modify: `src/bci_mcp/devices/__init__.py`
- Create: `tests/test_lsl_device.py`

Consume an LSL inlet. URI: `lsl://<name>` (resolve by name; empty → first EEG stream). The test creates an in-process LSL **outlet**, pushes samples, and reads them back through `LSLDevice` — a real round-trip, no hardware. `pylsl` via `pytest.importorskip`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_lsl_device.py`:

```python
import time

import pytest

pytest.importorskip("pylsl")

import numpy as np  # noqa: E402
from pylsl import StreamInfo, StreamOutlet  # noqa: E402

from bci_mcp.devices.lsl_device import LSLDevice  # noqa: E402


def test_lsl_roundtrip():
    info = StreamInfo("UnitTestEEG", "EEG", 2, 100.0, "float32", "uid-test-123")
    outlet = StreamOutlet(info)
    time.sleep(0.2)  # let the stream register

    dev = LSLDevice(name="UnitTestEEG")
    dev.connect()
    dev.start()
    for _ in range(50):
        outlet.push_sample([1.0, 2.0])
        time.sleep(0.005)

    chunk = None
    for _ in range(20):
        chunk = dev.read()
        if chunk is not None and chunk.data.shape[1] > 0:
            break
        time.sleep(0.05)
    dev.stop()
    dev.disconnect()

    assert chunk is not None
    assert chunk.data.shape[0] == 2
    assert dev.info.channel_count == 2
    assert dev.info.sample_rate == 100.0
    assert np.allclose(chunk.data[:, 0], [1.0, 2.0])
```

- [ ] **Step 2: Run test, confirm fail** — ModuleNotFoundError (install: `python3 -m pip install -e ".[lsl]"`).

- [ ] **Step 3: Implement**

Create `src/bci_mcp/devices/lsl_device.py`. **Verify the installed `pylsl` API** (`resolve_byprop`/`resolve_streams`, `StreamInlet.pull_chunk`) and adapt if needed.

```python
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
```

- [ ] **Step 4: Register on import** — add to `src/bci_mcp/devices/__init__.py`:

```python
try:  # pylsl is an optional dependency
    from . import lsl_device as _lsl_device  # noqa: F401
except Exception:  # pragma: no cover
    pass
```

- [ ] **Step 5: Run test, confirm pass** (with pylsl installed) — `python3 -m pytest tests/test_lsl_device.py -v` → 1 passed (or skipped if liblsl native lib unavailable; if skipped, note it).

- [ ] **Step 6: Commit** — `git add src/bci_mcp/devices/lsl_device.py src/bci_mcp/devices/__init__.py tests/test_lsl_device.py && git commit -m "feat: LSL inlet device (consume any Lab Streaming Layer stream)"`

---

### Task 6: Device discovery + CLI/MCP wiring

**Files:**
- Modify: `src/bci_mcp/core/registry.py` (add `list_schemes()` + `discover()`)
- Modify: `src/bci_mcp/cli.py` (`devices` lists real schemes + scanned serial ports)
- Modify: `src/bci_mcp/mcp/service.py` (`list_devices` returns the real scheme list)
- Create: `tests/test_discovery.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_discovery.py`:

```python
from bci_mcp.core.registry import discover, list_schemes


def test_list_schemes_includes_all_registered():
    schemes = list_schemes()
    for s in ("synthetic", "serial", "neurofocus", "brainflow", "lsl"):
        assert s in schemes


def test_discover_returns_entries_with_uris():
    entries = discover()
    assert any(e["uri"].startswith("synthetic://") for e in entries)
    for e in entries:
        assert "uri" in e and "name" in e
```

- [ ] **Step 2: Run test, confirm fail** — ImportError (`discover`/`list_schemes` not defined).

- [ ] **Step 3: Implement** in `src/bci_mcp/core/registry.py` (append):

```python
def list_schemes() -> list[str]:
    return sorted(_REGISTRY)


def discover() -> list[dict]:
    """Best-effort device discovery: always-available schemes + scanned serial ports."""
    entries: list[dict] = [
        {"uri": "synthetic://", "name": "Synthetic EEG (no hardware)",
         "needs_hardware": False},
    ]
    try:  # enumerate serial ports if pyserial is available
        from serial.tools import list_ports

        for port in list_ports.comports():
            entries.append({
                "uri": f"serial://{port.device}", "name": port.description or port.device,
                "needs_hardware": True,
            })
    except Exception:  # pragma: no cover
        pass
    return entries
```

- [ ] **Step 4: Wire CLI** — replace the body of `devices` in `src/bci_mcp/cli.py` to print `discover()` results plus the registered schemes from `list_schemes()`. Keep output containing `synthetic://` (so the Plan-1 CLI test still passes). Example:

```python
@app.command()
def devices() -> None:
    """List connectable EEG devices and URI schemes."""
    from .core.registry import discover, list_schemes

    console.print("[bold]Discovered devices:[/bold]")
    for entry in discover():
        console.print(f"  {entry['uri']:<28} {entry['name']}")
    console.print(f"\n[bold]URI schemes:[/bold] {', '.join(list_schemes())}")
    console.print("  e.g. neurofocus://ble/NEUROFOCUS_V4_01, brainflow://muse_s, "
                  "brainflow://cyton?serial_port=/dev/ttyUSB0, lsl://MyStream")
```

- [ ] **Step 5: Wire MCP service** — change `BrainService.list_devices` in `src/bci_mcp/mcp/service.py` to return discovery results:

```python
def list_devices(self) -> dict:
    from ..core.registry import discover, list_schemes

    return {"devices": discover(), "schemes": list_schemes()}
```

Update `tests/test_mcp_service.py::test_list_devices_includes_synthetic` if needed so it still asserts a synthetic entry is present (it checks `any("synthetic" in d["uri"] ...)`, which still holds).

- [ ] **Step 6: Run tests, confirm pass** — `python3 -m pytest tests/test_discovery.py tests/test_cli.py tests/test_mcp_service.py -v` → all pass.

- [ ] **Step 7: Full suite + ruff** — `ruff check src tests && python3 -m pytest` → all green (skips allowed for brainflow/pylsl if those native libs are unavailable; note any skips).

- [ ] **Step 8: Commit** — `git add -A && git commit -m "feat: device discovery + CLI/MCP wiring for all backends"`

---

## Self-review (plan author)

**Spec coverage:** NeuroFocus serial+BLE (Tasks 1,3) ✓; generic serial (Task 2) ✓; BrainFlow OpenBCI/Muse (Task 4) ✓; LSL (Task 5) ✓; discovery + CLI/MCP wiring (Task 6) ✓. All registered into the existing URI registry; all consumed by the existing `Pipeline`/MCP unchanged.

**Hardware-free testing:** NeuroFocus decode via byte fixtures (Task 1) + serial transport via fake serial (Tasks 2,3); BrainFlow via its synthetic board (Task 4); LSL via in-process outlet→inlet round-trip (Task 5). BLE live path is not unit-tested (no hardware) but its decode is covered and its construction/URI parsing are tested; flagged explicitly.

**Type consistency:** every backend returns `Chunk(data=(channels,n) float32 µV, timestamps=(n,))` and sets `DeviceInfo` with `units="uV"`, matching `Pipeline` expectations. Registry `register`/`create_device` unchanged; `list_schemes`/`discover` added.

**Adaptation guards:** bleak/brainflow/pylsl imported lazily; package import never hard-fails if an optional lib is missing; implementers instructed to verify each library's installed API and adapt.
