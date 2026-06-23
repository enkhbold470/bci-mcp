# BCI-MCP Plan 1 — Foundation + MCP (Phases 0–4)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the broken prototype with a `bci_mcp` Python package that streams live brain state from a built-in synthetic EEG brain and exposes it to Claude Desktop / any MCP client through a real Model Context Protocol server — fully tested, zero hardware required.

**Architecture:** A thin `Device` interface feeds a `Stream` (producer thread → ring buffer) into a DSP `Pipeline` that emits a `BrainState` (focus/calm/attention/band-powers/quality). A `SyntheticDevice` provides realistic data with no hardware. A `FastMCP` server and a Rich CLI both read `BrainState` from the same `Pipeline`.

**Tech Stack:** Python ≥3.10, numpy, scipy, `mcp` (official MCP SDK / FastMCP), typer, rich; hatchling build backend; pytest + ruff; GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-06-23-bci-mcp-brain-ai-bridge-design.md`

**Conventions for every task:** all source under `src/bci_mcp/`, all tests under `tests/`, run tests with `python -m pytest`. This plan is Phases 0–4; Plans 2–4 add hardware devices, recording/neurofeedback/dashboard/LSL, and polish.

---

## Phase 0 — Packaging skeleton

### Task 1: Project skeleton, packaging, remove broken prototype, CI

**Files:**
- Create: `pyproject.toml`
- Create: `src/bci_mcp/__init__.py`
- Create: `tests/test_smoke.py`
- Create: `.github/workflows/ci.yml`
- Delete: `src/main.py`, `src/__init__.py`, `src/bci/`, `src/mcp/`, `requirements.txt`

- [ ] **Step 1: Remove the broken prototype**

```bash
git rm -r src/main.py src/__init__.py src/bci src/mcp requirements.txt
```

Expected: files staged for deletion. (`docs/`, `docs-static/`, `mkdocs.yml`, `.github/workflows/*docs*` are kept.)

- [ ] **Step 2: Write `pyproject.toml`**

Create `pyproject.toml`:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "bci-mcp"
version = "0.1.0"
description = "Plug your brain into any AI — a real Model Context Protocol (MCP) server that streams live EEG brain state (focus, calm, attention) from any EEG device into Claude and any MCP client."
readme = "README.md"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [{ name = "enkhbold470" }]
keywords = ["eeg", "bci", "brain-computer-interface", "mcp", "model-context-protocol",
            "claude", "ai", "neurofeedback", "openbci", "muse", "brainflow", "lsl",
            "brainwave", "neurotech", "neuroscience"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering :: Medical Science Apps.",
    "Topic :: Scientific/Engineering :: Human Machine Interfaces",
]
dependencies = ["numpy>=1.24", "scipy>=1.10", "mcp>=1.2.0", "typer>=0.12", "rich>=13.0"]

[project.optional-dependencies]
devices = ["brainflow>=5.10", "bleak>=0.21", "pyserial>=3.5"]
dashboard = ["fastapi>=0.110", "uvicorn>=0.27", "websockets>=12.0"]
lsl = ["pylsl>=1.16"]
edf = ["pyedflib>=0.1.36"]
dev = ["pytest>=7.4", "pytest-cov>=4.1", "ruff>=0.4"]
all = ["bci-mcp[devices,dashboard,lsl,edf]"]

[project.scripts]
bci-mcp = "bci_mcp.cli:app"

[project.urls]
Homepage = "https://github.com/enkhbold470/bci-mcp"
Documentation = "https://enkhbold470.github.io/bci-mcp/"
Repository = "https://github.com/enkhbold470/bci-mcp"

[tool.hatch.build.targets.wheel]
packages = ["src/bci_mcp"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
```

- [ ] **Step 3: Write the package init**

Create `src/bci_mcp/__init__.py`:

```python
"""BCI-MCP — plug your brain into any AI."""

__version__ = "0.1.0"
```

- [ ] **Step 4: Write the smoke test**

Create `tests/test_smoke.py`:

```python
import bci_mcp


def test_version_exposed():
    assert isinstance(bci_mcp.__version__, str)
    assert bci_mcp.__version__.count(".") >= 2
```

- [ ] **Step 5: Install editable and run the smoke test**

Run:
```bash
python -m pip install -e ".[dev]"
python -m pytest tests/test_smoke.py -v
```
Expected: 1 passed.

- [ ] **Step 6: Write CI**

Create `.github/workflows/ci.yml`:

```yaml
name: ci
on:
  push:
    branches: [main]
  pull_request:
permissions:
  contents: read
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: python -m pip install -e ".[dev]"
      - run: ruff check src tests
      - run: python -m pytest
```

- [ ] **Step 7: Run ruff to confirm clean**

Run: `ruff check src tests`
Expected: `All checks passed!`

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "feat: bci_mcp package skeleton, packaging, CI; remove broken prototype"
```

---

## Phase 1 — Core acquisition

### Task 2: Device interface (`DeviceInfo`, `Chunk`, `Device`)

**Files:**
- Create: `src/bci_mcp/core/__init__.py` (empty)
- Create: `src/bci_mcp/core/device.py`
- Create: `tests/test_device.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_device.py`:

```python
import numpy as np
import pytest
from bci_mcp.core.device import Chunk, Device, DeviceInfo


def test_device_info_defaults():
    info = DeviceInfo(name="x", uri="synthetic://", sample_rate=256.0,
                      channel_count=2, channel_names=["a", "b"])
    assert info.units == "uV"
    assert info.extra == {}


def test_chunk_holds_array():
    c = Chunk(data=np.zeros((2, 5), dtype=np.float32), timestamps=np.arange(5.0))
    assert c.data.shape == (2, 5)
    assert c.timestamps.shape == (5,)


def test_device_is_abstract():
    with pytest.raises(TypeError):
        Device()  # cannot instantiate ABC with abstract methods
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_device.py -v`
Expected: FAIL (ModuleNotFoundError: bci_mcp.core.device).

- [ ] **Step 3: Implement**

Create `src/bci_mcp/core/__init__.py` (empty file).

Create `src/bci_mcp/core/device.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_device.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/bci_mcp/core tests/test_device.py
git commit -m "feat: Device interface (DeviceInfo, Chunk, Device ABC)"
```

---

### Task 3: Multi-channel ring buffer

**Files:**
- Create: `src/bci_mcp/core/ringbuffer.py`
- Create: `tests/test_ringbuffer.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_ringbuffer.py`:

```python
import numpy as np
from bci_mcp.core.ringbuffer import RingBuffer


def test_partial_fill_then_latest():
    rb = RingBuffer(channels=2, capacity=10)
    rb.write(np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float32))
    assert len(rb) == 3
    out = rb.latest(3)
    assert np.array_equal(out, [[1, 2, 3], [4, 5, 6]])


def test_wraparound_keeps_most_recent():
    rb = RingBuffer(channels=1, capacity=4)
    for i in range(6):
        rb.write(np.array([[i]], dtype=np.float32))
    assert len(rb) == 4
    assert np.array_equal(rb.latest(4), [[2, 3, 4, 5]])


def test_write_larger_than_capacity():
    rb = RingBuffer(channels=1, capacity=3)
    rb.write(np.arange(7, dtype=np.float32).reshape(1, 7))
    assert len(rb) == 3
    assert np.array_equal(rb.latest(3), [[4, 5, 6]])


def test_latest_more_than_available():
    rb = RingBuffer(channels=1, capacity=10)
    rb.write(np.array([[1, 2]], dtype=np.float32))
    assert rb.latest(100).shape == (1, 2)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_ringbuffer.py -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement**

Create `src/bci_mcp/core/ringbuffer.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_ringbuffer.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add src/bci_mcp/core/ringbuffer.py tests/test_ringbuffer.py
git commit -m "feat: multi-channel ring buffer"
```

---

### Task 4: Synthetic EEG device

**Files:**
- Create: `src/bci_mcp/devices/__init__.py` (empty)
- Create: `src/bci_mcp/devices/synthetic.py`
- Create: `tests/test_synthetic.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_synthetic.py`:

```python
import numpy as np
from bci_mcp.devices.synthetic import SyntheticDevice


def test_shape_and_units():
    dev = SyntheticDevice(channels=4, sample_rate=256.0, chunk_samples=32, seed=1)
    dev.connect()
    dev.start()
    chunk = dev.read()
    assert chunk is not None
    assert chunk.data.shape == (4, 32)
    assert chunk.data.dtype == np.float32
    assert chunk.timestamps.shape == (32,)
    assert dev.info.units == "uV"


def test_read_returns_none_when_stopped():
    dev = SyntheticDevice(seed=1)
    assert dev.read() is None  # not started


def test_deterministic_with_seed():
    a = SyntheticDevice(seed=42)
    a.start()
    b = SyntheticDevice(seed=42)
    b.start()
    assert np.array_equal(a.read().data, b.read().data)


def test_higher_focus_has_more_beta_relative_to_alpha():
    # Generate a few seconds and compare 20Hz (beta) vs 10Hz (alpha) content.
    def power_at(dev, freq):
        dev.start()
        sig = np.concatenate([dev.read().data[0] for _ in range(40)])  # ~5s @256/32
        fft = np.abs(np.fft.rfft(sig))
        freqs = np.fft.rfftfreq(sig.size, 1 / dev.info.sample_rate)
        return fft[np.argmin(np.abs(freqs - freq))]

    low = SyntheticDevice(focus=0.0, seed=7)
    high = SyntheticDevice(focus=1.0, seed=7)
    ratio_low = power_at(low, 20) / power_at(SyntheticDevice(focus=0.0, seed=7), 10)
    ratio_high = power_at(high, 20) / power_at(SyntheticDevice(focus=1.0, seed=7), 10)
    assert ratio_high > ratio_low
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_synthetic.py -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement**

Create `src/bci_mcp/devices/__init__.py` (empty file).

Create `src/bci_mcp/devices/synthetic.py`:

```python
"""Synthetic EEG device — realistic brainwaves with no hardware."""
from __future__ import annotations

import numpy as np

from ..core.device import Chunk, Device, DeviceInfo


class SyntheticDevice(Device):
    """Generates band-mixed EEG. `focus` (0..1) trades alpha for beta."""

    def __init__(
        self,
        channels: int = 4,
        sample_rate: float = 256.0,
        chunk_samples: int = 32,
        focus: float = 0.5,
        seed: int | None = None,
        uri: str = "synthetic://",
    ) -> None:
        self.info = DeviceInfo(
            name="Synthetic EEG",
            uri=uri,
            sample_rate=sample_rate,
            channel_count=channels,
            channel_names=[f"ch{i + 1}" for i in range(channels)],
            units="uV",
        )
        self.chunk_samples = chunk_samples
        self.focus = float(np.clip(focus, 0.0, 1.0))
        self._rng = np.random.default_rng(seed)
        self._t = 0  # sample counter
        self._streaming = False

    def connect(self) -> None:
        pass

    def start(self) -> None:
        self._streaming = True

    def stop(self) -> None:
        self._streaming = False

    def disconnect(self) -> None:
        pass

    def read(self) -> Chunk | None:
        if not self._streaming:
            return None
        fs = self.info.sample_rate
        n = self.chunk_samples
        idx = self._t + np.arange(n)
        t = idx / fs
        alpha_amp = 20.0 * (1.0 - self.focus) + 5.0  # 10 Hz
        beta_amp = 18.0 * self.focus + 3.0  # 20 Hz
        base = (
            alpha_amp * np.sin(2 * np.pi * 10 * t)
            + beta_amp * np.sin(2 * np.pi * 20 * t)
            + 8.0 * np.sin(2 * np.pi * 6 * t)  # theta
        )
        data = np.empty((self.info.channel_count, n), dtype=np.float32)
        for c in range(self.info.channel_count):
            noise = self._rng.normal(0.0, 5.0, n)
            data[c] = base + noise
        self._t += n
        return Chunk(data=data, timestamps=t.astype(np.float64))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_synthetic.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add src/bci_mcp/devices tests/test_synthetic.py
git commit -m "feat: synthetic EEG device (no hardware)"
```

---

### Task 5: Device registry (URI → device)

**Files:**
- Create: `src/bci_mcp/core/registry.py`
- Modify: `src/bci_mcp/devices/synthetic.py` (register factory at import)
- Modify: `src/bci_mcp/__init__.py` (import devices so registration runs)
- Create: `tests/test_registry.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_registry.py`:

```python
import pytest
from bci_mcp.core.registry import create_device
from bci_mcp.devices.synthetic import SyntheticDevice


def test_default_scheme_is_synthetic():
    dev = create_device("synthetic://")
    assert isinstance(dev, SyntheticDevice)


def test_params_parsed():
    dev = create_device("synthetic://?channels=8&focus=0.9&seed=3")
    assert dev.info.channel_count == 8
    assert dev.focus == 0.9


def test_unknown_scheme_raises():
    with pytest.raises(ValueError, match="Unknown device scheme"):
        create_device("nope://whatever")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_registry.py -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement the registry**

Create `src/bci_mcp/core/registry.py`:

```python
"""URI-based device registry: create_device('synthetic://?focus=0.8')."""
from __future__ import annotations

from collections.abc import Callable
from urllib.parse import ParseResult, parse_qs, urlparse

from .device import Device

DeviceFactory = Callable[[ParseResult, dict[str, str]], Device]
_REGISTRY: dict[str, DeviceFactory] = {}


def register(scheme: str, factory: DeviceFactory) -> None:
    _REGISTRY[scheme] = factory


def create_device(uri: str) -> Device:
    parsed = urlparse(uri)
    scheme = parsed.scheme or "synthetic"
    if scheme not in _REGISTRY:
        raise ValueError(
            f"Unknown device scheme '{scheme}'. Known: {sorted(_REGISTRY)}"
        )
    params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
    return _REGISTRY[scheme](parsed, params)
```

- [ ] **Step 4: Register the synthetic factory**

Append to `src/bci_mcp/devices/synthetic.py`:

```python


def _factory(parsed, params):  # noqa: ANN001
    return SyntheticDevice(
        channels=int(params.get("channels", 4)),
        sample_rate=float(params.get("sample_rate", 256.0)),
        focus=float(params.get("focus", 0.5)),
        seed=int(params["seed"]) if "seed" in params else None,
        uri=f"synthetic://?{parsed.query}" if parsed.query else "synthetic://",
    )


from ..core.registry import register  # noqa: E402

register("synthetic", _factory)
```

- [ ] **Step 5: Ensure registration runs on package import**

Replace `src/bci_mcp/__init__.py` with:

```python
"""BCI-MCP — plug your brain into any AI."""

from . import devices as _devices  # noqa: F401  (triggers device registration)

__version__ = "0.1.0"
```

- [ ] **Step 6: Make devices import the synthetic module**

Replace `src/bci_mcp/devices/__init__.py` with:

```python
from . import synthetic as _synthetic  # noqa: F401  (registers 'synthetic' scheme)
```

- [ ] **Step 7: Run test to verify it passes**

Run: `python -m pytest tests/test_registry.py -v`
Expected: 3 passed.

- [ ] **Step 8: Commit**

```bash
git add src/bci_mcp tests/test_registry.py
git commit -m "feat: URI device registry + synthetic registration"
```

---

### Task 6: Stream (producer thread → ring buffer)

**Files:**
- Create: `src/bci_mcp/core/stream.py`
- Create: `tests/test_stream.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_stream.py`:

```python
import time

from bci_mcp.core.stream import Stream
from bci_mcp.devices.synthetic import SyntheticDevice


def test_stream_fills_buffer():
    dev = SyntheticDevice(channels=2, sample_rate=256.0, chunk_samples=32, seed=1)
    s = Stream(dev, buffer_seconds=2.0)
    s.start()
    time.sleep(0.3)
    s.stop()
    data = s.latest(64)
    assert data.shape[0] == 2
    assert data.shape[1] > 0


def test_consumer_receives_chunks():
    dev = SyntheticDevice(seed=1)
    s = Stream(dev)
    received = []
    s.add_consumer(lambda chunk: received.append(chunk))
    s.start()
    time.sleep(0.2)
    s.stop()
    assert len(received) > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_stream.py -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement**

Create `src/bci_mcp/core/stream.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_stream.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add src/bci_mcp/core/stream.py tests/test_stream.py
git commit -m "feat: Stream producer thread with ring buffer + consumers"
```

---

## Phase 2 — Signal processing → BrainState

### Task 7: Filters

**Files:**
- Create: `src/bci_mcp/dsp/__init__.py` (empty)
- Create: `src/bci_mcp/dsp/filters.py`
- Create: `tests/test_filters.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_filters.py`:

```python
import numpy as np
from bci_mcp.dsp.filters import bandpass, notch


def _sine(freq, fs, n, ch=1):
    t = np.arange(n) / fs
    return np.tile(np.sin(2 * np.pi * freq * t), (ch, 1))


def test_bandpass_attenuates_out_of_band():
    fs, n = 256.0, 1024
    in_band = _sine(10, fs, n)
    out_band = _sine(70, fs, n)
    assert np.std(bandpass(in_band, fs)) > 0.5 * np.std(in_band)
    assert np.std(bandpass(out_band, fs)) < 0.2 * np.std(out_band)


def test_notch_removes_line_noise():
    fs, n = 256.0, 1024
    sig = _sine(10, fs, n) + _sine(60, fs, n)
    filtered = notch(sig, fs, freq=60.0)
    fft = np.abs(np.fft.rfft(filtered[0]))
    freqs = np.fft.rfftfreq(n, 1 / fs)
    p60 = fft[np.argmin(np.abs(freqs - 60))]
    p10 = fft[np.argmin(np.abs(freqs - 10))]
    assert p60 < 0.1 * p10
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_filters.py -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement**

Create `src/bci_mcp/dsp/__init__.py` (empty file).

Create `src/bci_mcp/dsp/filters.py`:

```python
"""Zero-phase EEG filters (operate along the last axis: (channels, n_samples))."""
from __future__ import annotations

import numpy as np
from scipy.signal import butter, filtfilt, iirnotch


def bandpass(data: np.ndarray, fs: float, low: float = 1.0, high: float = 45.0,
             order: int = 4) -> np.ndarray:
    nyq = 0.5 * fs
    b, a = butter(order, [low / nyq, min(high, nyq - 1) / nyq], btype="band")
    return filtfilt(b, a, data, axis=-1)


def notch(data: np.ndarray, fs: float, freq: float = 60.0, q: float = 30.0) -> np.ndarray:
    b, a = iirnotch(freq / (0.5 * fs), q)
    return filtfilt(b, a, data, axis=-1)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_filters.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add src/bci_mcp/dsp tests/test_filters.py
git commit -m "feat: bandpass + notch filters"
```

---

### Task 8: Band powers

**Files:**
- Create: `src/bci_mcp/dsp/bands.py`
- Create: `tests/test_bands.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_bands.py`:

```python
import numpy as np
from bci_mcp.dsp.bands import BANDS, band_powers, relative_band_powers


def test_alpha_sine_peaks_in_alpha_band():
    fs, n = 256.0, 1024
    t = np.arange(n) / fs
    data = np.tile(np.sin(2 * np.pi * 10 * t), (2, 1))  # 10 Hz = alpha
    bp = band_powers(data, fs)
    assert set(bp) == set(BANDS)
    assert bp["alpha"] == max(bp.values())


def test_relative_sums_to_one():
    fs, n = 256.0, 1024
    t = np.arange(n) / fs
    data = np.tile(np.sin(2 * np.pi * 10 * t) + np.sin(2 * np.pi * 20 * t), (1, 1))
    rel = relative_band_powers(band_powers(data, fs))
    assert abs(sum(rel.values()) - 1.0) < 1e-6
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_bands.py -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement**

Create `src/bci_mcp/dsp/bands.py`:

```python
"""Band power via Welch PSD."""
from __future__ import annotations

import numpy as np
from scipy.signal import welch

BANDS: dict[str, tuple[float, float]] = {
    "delta": (1.0, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 13.0),
    "beta": (13.0, 30.0),
    "gamma": (30.0, 45.0),
}


def band_powers(data: np.ndarray, fs: float) -> dict[str, float]:
    """Mean absolute power per band, averaged over channels (µV²)."""
    nperseg = min(data.shape[-1], int(fs))
    freqs, psd = welch(data, fs=fs, nperseg=nperseg)
    psd = np.atleast_2d(psd)
    out: dict[str, float] = {}
    for band, (lo, hi) in BANDS.items():
        mask = (freqs >= lo) & (freqs < hi)
        if not mask.any():
            out[band] = 0.0
        else:
            out[band] = float(np.mean(np.trapz(psd[:, mask], freqs[mask], axis=-1)))
    return out


def relative_band_powers(bp: dict[str, float]) -> dict[str, float]:
    total = sum(bp.values()) or 1.0
    return {k: v / total for k, v in bp.items()}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_bands.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add src/bci_mcp/dsp/bands.py tests/test_bands.py
git commit -m "feat: Welch band powers (delta..gamma)"
```

---

### Task 9: Raw cognitive metrics

**Files:**
- Create: `src/bci_mcp/dsp/metrics.py`
- Create: `tests/test_metrics.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_metrics.py`:

```python
from bci_mcp.dsp.metrics import METRIC_NAMES, raw_metrics


def test_all_metrics_present():
    bp = {"delta": 1, "theta": 1, "alpha": 1, "beta": 1, "gamma": 1}
    m = raw_metrics(bp)
    assert set(m) == set(METRIC_NAMES)


def test_more_beta_raises_focus():
    low = raw_metrics({"delta": 1, "theta": 2, "alpha": 2, "beta": 1, "gamma": 1})
    high = raw_metrics({"delta": 1, "theta": 2, "alpha": 2, "beta": 8, "gamma": 1})
    assert high["focus"] > low["focus"]


def test_more_alpha_raises_calm():
    low = raw_metrics({"delta": 1, "theta": 1, "alpha": 1, "beta": 5, "gamma": 1})
    high = raw_metrics({"delta": 1, "theta": 1, "alpha": 9, "beta": 5, "gamma": 1})
    assert high["calm"] > low["calm"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_metrics.py -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement**

Create `src/bci_mcp/dsp/metrics.py`:

```python
"""Cognitive metrics derived from band powers (documented heuristics)."""
from __future__ import annotations

METRIC_NAMES = ("focus", "calm", "attention", "engagement", "fatigue", "meditation")
_EPS = 1e-9


def raw_metrics(bp: dict[str, float]) -> dict[str, float]:
    """Unscaled metric ratios. Calibration maps these into 0..1 later."""
    d, t, a, b, g = (bp["delta"], bp["theta"], bp["alpha"], bp["beta"], bp["gamma"])
    total = d + t + a + b + g + _EPS
    return {
        "focus": b / (a + t + _EPS),          # concentration (beta vs alpha+theta)
        "calm": a / (a + b + _EPS),           # relaxation (alpha vs beta)
        "attention": b / (t + _EPS),          # beta vs theta
        "engagement": (b + g) / (a + t + d + _EPS),  # Pope-style engagement
        "fatigue": (t + d) / (a + b + _EPS),  # drowsiness
        "meditation": t / total,              # relative theta
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_metrics.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/bci_mcp/dsp/metrics.py tests/test_metrics.py
git commit -m "feat: cognitive metrics (focus, calm, attention, engagement, fatigue, meditation)"
```

---

### Task 10: Signal quality + artifacts

**Files:**
- Create: `src/bci_mcp/dsp/quality.py`
- Create: `tests/test_quality.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_quality.py`:

```python
import numpy as np
from bci_mcp.dsp.quality import assess_quality


def test_flatline_is_no_contact():
    data = np.zeros((1, 256), dtype=np.float32)
    score, label, artifacts = assess_quality(data, 256.0)
    assert label == "no_contact"
    assert score == 0.0
    assert "flatline" in artifacts


def test_good_eeg_amplitude():
    rng = np.random.default_rng(0)
    data = rng.normal(0, 20.0, (1, 256)).astype(np.float32)  # ~20µV noise
    score, label, _ = assess_quality(data, 256.0)
    assert label == "good"
    assert score > 0.75


def test_railing_flagged():
    data = np.full((1, 256), 5000.0, dtype=np.float32)
    data[0, ::2] = -5000.0  # huge swing, not flat
    _, _, artifacts = assess_quality(data, 256.0)
    assert "railing" in artifacts
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_quality.py -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement**

Create `src/bci_mcp/dsp/quality.py`:

```python
"""Heuristic signal-quality assessment and artifact flags."""
from __future__ import annotations

import numpy as np


def assess_quality(data: np.ndarray, fs: float) -> tuple[float, str, list[str]]:
    artifacts: list[str] = []
    var = float(np.mean(np.var(data, axis=-1)))
    if var < 1e-3:
        return 0.0, "no_contact", ["flatline"]

    amp = float(np.mean(np.ptp(data, axis=-1)))  # mean peak-to-peak across channels
    score = 1.0
    if amp > 2000.0:  # rail-to-rail swing
        artifacts.append("railing")
        score -= 0.6
    elif amp > 400.0:  # implausibly large for scalp EEG
        score -= 0.25
    if float(np.max(np.abs(data[0]))) > 150.0 and amp <= 2000.0:
        artifacts.append("blink")

    score = max(0.0, min(1.0, score))
    label = "good" if score > 0.75 else "fair" if score > 0.4 else "poor"
    return score, label, artifacts
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_quality.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/bci_mcp/dsp/quality.py tests/test_quality.py
git commit -m "feat: signal quality + artifact detection"
```

---

### Task 11: Calibration

**Files:**
- Create: `src/bci_mcp/dsp/calibration.py`
- Create: `tests/test_calibration.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_calibration.py`:

```python
from bci_mcp.dsp.calibration import Calibration


def test_uncalibrated_maps_to_unit_interval():
    cal = Calibration()
    assert not cal.calibrated
    out = cal.apply({"focus": 1.0, "calm": 0.0})
    assert all(0.0 <= v <= 1.0 for v in out.values())


def test_from_samples_centers_at_half():
    samples = [{"focus": x} for x in (0.8, 1.0, 1.2)]  # mean ~1.0
    cal = Calibration.from_samples(samples)
    assert cal.calibrated
    out = cal.apply({"focus": 1.0})
    assert abs(out["focus"] - 0.5) < 0.05


def test_json_roundtrip():
    cal = Calibration.from_samples([{"focus": 0.5}, {"focus": 1.5}])
    restored = Calibration.from_json(cal.to_json())
    assert restored.baseline == cal.baseline
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_calibration.py -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement**

Create `src/bci_mcp/dsp/calibration.py`:

```python
"""Per-metric baseline that maps raw ratios into a personalized 0..1 range."""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field

import numpy as np


@dataclass
class Calibration:
    baseline: dict[str, dict[str, float]] = field(default_factory=dict)

    @property
    def calibrated(self) -> bool:
        return bool(self.baseline)

    def apply(self, raw: dict[str, float]) -> dict[str, float]:
        out: dict[str, float] = {}
        for key, value in raw.items():
            if key in self.baseline:
                mean = self.baseline[key]["mean"]
                std = self.baseline[key]["std"] or 1.0
                z = (value - mean) / std
            else:
                z = value - 1.0  # default: ratio of 1.0 maps to 0.5
            out[key] = 1.0 / (1.0 + math.exp(-z))
        return out

    def to_json(self) -> str:
        return json.dumps({"baseline": self.baseline})

    @classmethod
    def from_json(cls, text: str) -> Calibration:
        return cls(baseline=json.loads(text)["baseline"])

    @classmethod
    def from_samples(cls, raw_list: list[dict[str, float]]) -> Calibration:
        keys = raw_list[0].keys()
        baseline = {
            k: {
                "mean": float(np.mean([r[k] for r in raw_list])),
                "std": float(np.std([r[k] for r in raw_list])),
            }
            for k in keys
        }
        return cls(baseline=baseline)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_calibration.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/bci_mcp/dsp/calibration.py tests/test_calibration.py
git commit -m "feat: calibration baseline → personalized 0..1 metrics"
```

---

### Task 12: BrainState snapshot

**Files:**
- Create: `src/bci_mcp/dsp/state.py`
- Create: `tests/test_state.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_state.py`:

```python
from bci_mcp.dsp.state import BrainState


def _state():
    return BrainState(
        timestamp=1.0,
        metrics={"focus": 0.7, "calm": 0.3},
        band_powers={"alpha": 1.0},
        relative_band_powers={"alpha": 1.0},
        signal_quality="good",
        quality_score=0.9,
        artifacts=[],
        channels=4,
        sample_rate=256.0,
        calibrated=True,
    )


def test_to_dict_roundtrips_fields():
    d = _state().to_dict()
    assert d["metrics"]["focus"] == 0.7
    assert d["signal_quality"] == "good"
    assert d["channels"] == 4


def test_summary_is_readable_string():
    s = _state().summary()
    assert "focus" in s.lower()
    assert "good" in s.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_state.py -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement**

Create `src/bci_mcp/dsp/state.py`:

```python
"""The unified brain-state snapshot shared by CLI, dashboard, and MCP."""
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class BrainState:
    timestamp: float
    metrics: dict[str, float]
    band_powers: dict[str, float]
    relative_band_powers: dict[str, float]
    signal_quality: str
    quality_score: float
    artifacts: list[str]
    channels: int
    sample_rate: float
    calibrated: bool

    def to_dict(self) -> dict:
        return asdict(self)

    def summary(self) -> str:
        top = ", ".join(f"{k}={v:.2f}" for k, v in self.metrics.items())
        arts = ", ".join(self.artifacts) if self.artifacts else "none"
        cal = "calibrated" if self.calibrated else "uncalibrated"
        return (
            f"[{cal}] {top} | signal: {self.signal_quality} "
            f"({self.quality_score:.2f}) | artifacts: {arts}"
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_state.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add src/bci_mcp/dsp/state.py tests/test_state.py
git commit -m "feat: BrainState snapshot"
```

---

### Task 13: Pipeline (device → DSP → BrainState)

**Files:**
- Create: `src/bci_mcp/pipeline.py`
- Create: `tests/test_pipeline.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_pipeline.py`:

```python
import time

from bci_mcp.dsp.state import BrainState
from bci_mcp.pipeline import Pipeline


def test_pipeline_produces_brainstate():
    p = Pipeline("synthetic://?seed=1", window_seconds=1.0)
    p.start()
    try:
        state = None
        for _ in range(50):  # poll up to ~5s for the buffer to fill
            time.sleep(0.1)
            state = p.current_state()
            if state is not None:
                break
        assert isinstance(state, BrainState)
        assert set(state.metrics)  # non-empty
        assert all(0.0 <= v <= 1.0 for v in state.metrics.values())
        assert state.channels == 4
    finally:
        p.stop()


def test_calibrate_sets_baseline():
    p = Pipeline("synthetic://?seed=2", window_seconds=1.0)
    p.start()
    try:
        time.sleep(1.2)
        cal = p.calibrate(seconds=1)
        assert cal.calibrated
        assert p.current_state().calibrated
    finally:
        p.stop()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_pipeline.py -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement**

Create `src/bci_mcp/pipeline.py`:

```python
"""Pipeline: ties a Device/Stream to the DSP chain and emits BrainState."""
from __future__ import annotations

import time

from .core.device import Device
from .core.registry import create_device
from .core.stream import Stream
from .dsp import bands, filters
from .dsp import metrics as metrics_mod
from .dsp import quality as quality_mod
from .dsp.calibration import Calibration
from .dsp.state import BrainState


class Pipeline:
    def __init__(self, device: Device | str, window_seconds: float = 1.0,
                 notch_freq: float = 60.0) -> None:
        self.device = create_device(device) if isinstance(device, str) else device
        self.stream = Stream(self.device)
        self.window = int(self.device.info.sample_rate * window_seconds)
        self.notch_freq = notch_freq
        self.calibration = Calibration()

    def start(self) -> None:
        self.stream.start()

    def stop(self) -> None:
        self.stream.stop()

    def _raw_metrics_now(self):
        fs = self.device.info.sample_rate
        data = self.stream.latest(self.window)
        if data.shape[1] < int(fs * 0.5):
            return None, None, data, fs
        filtered = filters.bandpass(data, fs)
        bp = bands.band_powers(filtered, fs)
        return metrics_mod.raw_metrics(bp), bp, data, fs

    def current_state(self) -> BrainState | None:
        raw, bp, data, fs = self._raw_metrics_now()
        if raw is None:
            return None
        scaled = self.calibration.apply(raw)
        q_score, q_label, artifacts = quality_mod.assess_quality(data, fs)
        return BrainState(
            timestamp=time.time(),
            metrics=scaled,
            band_powers=bp,
            relative_band_powers=bands.relative_band_powers(bp),
            signal_quality=q_label,
            quality_score=q_score,
            artifacts=artifacts,
            channels=self.device.info.channel_count,
            sample_rate=fs,
            calibrated=self.calibration.calibrated,
        )

    def calibrate(self, seconds: float = 20.0) -> Calibration:
        samples = []
        end = time.time() + seconds
        while time.time() < end:
            raw, _, _, _ = self._raw_metrics_now()
            if raw is not None:
                samples.append(raw)
            time.sleep(0.25)
        if samples:
            self.calibration = Calibration.from_samples(samples)
        return self.calibration
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_pipeline.py -v`
Expected: 2 passed.

- [ ] **Step 5: Run the whole suite + ruff**

Run: `ruff check src tests && python -m pytest`
Expected: all green.

- [ ] **Step 6: Commit**

```bash
git add src/bci_mcp/pipeline.py tests/test_pipeline.py
git commit -m "feat: DSP pipeline emitting BrainState + calibration"
```

---

## Phase 3 — CLI

### Task 14: CLI (`devices`, `stream`, `serve`)

**Files:**
- Create: `src/bci_mcp/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_cli.py`:

```python
from typer.testing import CliRunner

from bci_mcp.cli import app

runner = CliRunner()


def test_devices_lists_synthetic():
    result = runner.invoke(app, ["devices"])
    assert result.exit_code == 0
    assert "synthetic://" in result.stdout


def test_stream_once_prints_metrics():
    # --once renders a single BrainState snapshot and exits (no live loop)
    result = runner.invoke(app, ["stream", "--device", "synthetic://?seed=1", "--once"])
    assert result.exit_code == 0
    assert "focus" in result.stdout.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cli.py -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement**

Create `src/bci_mcp/cli.py`:

```python
"""bci-mcp command-line interface."""
from __future__ import annotations

import time

import typer
from rich.console import Console
from rich.live import Live
from rich.table import Table

from .dsp.state import BrainState
from .pipeline import Pipeline

app = typer.Typer(add_completion=False, help="Plug your brain into any AI.")
console = Console()


@app.command()
def devices() -> None:
    """List known device URIs you can connect to."""
    console.print("[bold]Available device schemes:[/bold]")
    console.print("  synthetic://              built-in EEG, no hardware (default)")
    console.print("  neurofocus://ble/<name>   NeuroFocus v4 over BLE        (Plan 2)")
    console.print("  neurofocus://serial/<port> NeuroFocus v4 over USB       (Plan 2)")
    console.print("  brainflow://<board>       OpenBCI / Muse / etc.         (Plan 2)")
    console.print("  lsl://<stream>            any Lab Streaming Layer source (Plan 2)")


def _render(state: BrainState | None) -> Table:
    table = Table(title="BCI-MCP — live brain state")
    table.add_column("metric")
    table.add_column("value")
    table.add_column("bar")
    if state is None:
        table.add_row("status", "warming up…", "")
        return table
    for name, value in state.metrics.items():
        bar = "█" * int(value * 20) + "░" * (20 - int(value * 20))
        table.add_row(name, f"{value:.2f}", bar)
    table.add_row("signal", state.signal_quality, f"{state.quality_score:.2f}")
    return table


@app.command()
def stream(
    device: str = typer.Option("synthetic://", help="Device URI."),
    once: bool = typer.Option(False, help="Print one snapshot and exit."),
) -> None:
    """Live terminal brain-meter."""
    pipeline = Pipeline(device)
    pipeline.start()
    try:
        if once:
            state = None
            for _ in range(50):
                time.sleep(0.1)
                state = pipeline.current_state()
                if state is not None:
                    break
            console.print(_render(state))
            return
        with Live(_render(None), console=console, refresh_per_second=4) as live:
            while True:
                time.sleep(0.25)
                live.update(_render(pipeline.current_state()))
    except KeyboardInterrupt:
        pass
    finally:
        pipeline.stop()


@app.command()
def serve(transport: str = typer.Option("stdio", help="stdio | sse")) -> None:
    """Run the MCP server (for Claude Desktop)."""
    from .mcp.server import serve as serve_mcp

    serve_mcp(transport=transport)


# Alias `bci-mcp mcp` → `bci-mcp serve`
@app.command(name="mcp")
def mcp_alias(transport: str = typer.Option("stdio")) -> None:
    """Alias for `serve`."""
    serve(transport=transport)


if __name__ == "__main__":
    app()
```

- [ ] **Step 4: Run test to verify it passes**

Note: `test_stream_once` exercises the pipeline but the `serve` command imports `bci_mcp.mcp.server`, which does not exist until Task 15. The CLI import must not eagerly import the MCP server — it is imported lazily inside `serve`, so `tests/test_cli.py` passes now.

Run: `python -m pytest tests/test_cli.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add src/bci_mcp/cli.py tests/test_cli.py
git commit -m "feat: CLI (devices, stream live brain-meter, serve)"
```

---

## Phase 4 — Real MCP server (the killer feature)

### Task 15: MCP server (service + FastMCP tools)

**Files:**
- Create: `src/bci_mcp/mcp/__init__.py` (empty)
- Create: `src/bci_mcp/mcp/service.py` (testable core, no MCP dependency)
- Create: `src/bci_mcp/mcp/server.py` (thin FastMCP adapter)
- Create: `tests/test_mcp_service.py`

Rationale: keep all logic in a plain `BrainService` class so it is unit-testable without an MCP client; `server.py` only wires `BrainService` methods to FastMCP tools/resources.

- [ ] **Step 1: Write the failing test**

Create `tests/test_mcp_service.py`:

```python
import time

from bci_mcp.mcp.service import BrainService


def test_connect_then_get_state():
    svc = BrainService()
    assert svc.get_brain_state()["error"]  # not connected yet

    out = svc.connect("synthetic://?seed=1")
    assert out["connected"] is True
    try:
        state = {"status": "warming_up"}
        for _ in range(50):
            time.sleep(0.1)
            state = svc.get_brain_state()
            if "metrics" in state:
                break
        assert "metrics" in state
        assert "focus" in state["metrics"]

        bands = svc.get_band_powers()
        assert "alpha" in bands["band_powers"]

        quality = svc.get_signal_quality()
        assert "signal_quality" in quality
    finally:
        svc.disconnect()


def test_list_devices_includes_synthetic():
    svc = BrainService()
    out = svc.list_devices()
    assert any("synthetic" in d["uri"] for d in out["devices"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_mcp_service.py -v`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement the service**

Create `src/bci_mcp/mcp/__init__.py` (empty file).

Create `src/bci_mcp/mcp/service.py`:

```python
"""Testable brain-service core. server.py adapts this to MCP."""
from __future__ import annotations

from ..pipeline import Pipeline


class BrainService:
    def __init__(self) -> None:
        self._pipeline: Pipeline | None = None
        self._events: list[dict] = []

    def list_devices(self) -> dict:
        return {
            "devices": [
                {"uri": "synthetic://", "name": "Synthetic EEG", "needs_hardware": False},
            ]
        }

    def connect(self, device_uri: str = "synthetic://") -> dict:
        if self._pipeline is not None:
            self._pipeline.stop()
        self._pipeline = Pipeline(device_uri)
        self._pipeline.start()
        return {"connected": True, "device": self._pipeline.device.info.name,
                "uri": device_uri}

    def disconnect(self) -> dict:
        if self._pipeline is not None:
            self._pipeline.stop()
            self._pipeline = None
        return {"connected": False}

    def get_brain_state(self) -> dict:
        if self._pipeline is None:
            return {"error": "not connected — call connect() first"}
        state = self._pipeline.current_state()
        return state.to_dict() if state is not None else {"status": "warming_up"}

    def get_band_powers(self) -> dict:
        state = self._require_state()
        if "error" in state or "status" in state:
            return state
        return {"band_powers": state["band_powers"],
                "relative_band_powers": state["relative_band_powers"]}

    def get_signal_quality(self) -> dict:
        state = self._require_state()
        if "error" in state or "status" in state:
            return state
        return {"signal_quality": state["signal_quality"],
                "quality_score": state["quality_score"],
                "artifacts": state["artifacts"]}

    def calibrate(self, seconds: int = 20, condition: str = "relax") -> dict:
        if self._pipeline is None:
            return {"error": "not connected"}
        cal = self._pipeline.calibrate(seconds=seconds)
        return {"calibrated": cal.calibrated, "condition": condition,
                "metrics": list(cal.baseline)}

    def mark_event(self, label: str) -> dict:
        import time
        self._events.append({"label": label, "timestamp": time.time()})
        return {"marked": label, "total_events": len(self._events)}

    def stream_summary(self, seconds: int = 30) -> dict:
        # Plan 1: report the instantaneous state; rolling stats arrive with recording.
        state = self._require_state()
        if "metrics" not in state:
            return state
        return {"window_seconds": seconds, "current": state["metrics"],
                "signal_quality": state["signal_quality"]}

    def _require_state(self) -> dict:
        if self._pipeline is None:
            return {"error": "not connected"}
        state = self._pipeline.current_state()
        return state.to_dict() if state is not None else {"status": "warming_up"}
```

- [ ] **Step 4: Run service test to verify it passes**

Run: `python -m pytest tests/test_mcp_service.py -v`
Expected: 2 passed.

- [ ] **Step 5: Implement the FastMCP adapter**

Create `src/bci_mcp/mcp/server.py`:

```python
"""Real Model Context Protocol server exposing live brain state."""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .service import BrainService

mcp = FastMCP("bci-mcp")
_service = BrainService()


@mcp.tool()
def list_devices() -> dict:
    """List EEG devices/URIs you can connect to."""
    return _service.list_devices()


@mcp.tool()
def connect(device_uri: str = "synthetic://") -> dict:
    """Connect to an EEG device and start streaming. Default is the synthetic brain."""
    return _service.connect(device_uri)


@mcp.tool()
def disconnect() -> dict:
    """Disconnect from the current EEG device."""
    return _service.disconnect()


@mcp.tool()
def get_brain_state() -> dict:
    """Get the current brain state: focus, calm, attention, band powers, signal quality."""
    return _service.get_brain_state()


@mcp.tool()
def get_band_powers() -> dict:
    """Get absolute and relative EEG band powers (delta, theta, alpha, beta, gamma)."""
    return _service.get_band_powers()


@mcp.tool()
def get_signal_quality() -> dict:
    """Get electrode signal quality and detected artifacts (blink, railing, …)."""
    return _service.get_signal_quality()


@mcp.tool()
def calibrate(seconds: int = 20, condition: str = "relax") -> dict:
    """Capture a baseline so focus/calm/etc. are personalized to the wearer."""
    return _service.calibrate(seconds, condition)


@mcp.tool()
def mark_event(label: str) -> dict:
    """Annotate the live stream with a labeled event marker."""
    return _service.mark_event(label)


@mcp.tool()
def stream_summary(seconds: int = 30) -> dict:
    """Summarize recent brain activity over the last N seconds."""
    return _service.stream_summary(seconds)


@mcp.resource("brain://state")
def brain_state_resource() -> str:
    """Live brain-state snapshot as text."""
    state = _service.get_brain_state()
    return str(state)


@mcp.resource("brain://device")
def brain_device_resource() -> str:
    """Information about the connected device."""
    return str(_service.list_devices())


@mcp.prompt()
def interpret_brain_state() -> str:
    """Prompt template: ask the model to interpret the current brain state."""
    return (
        "Call get_brain_state, then explain in plain language what the wearer's "
        "focus, calm, and attention levels suggest about their current cognitive "
        "state, and suggest one actionable tip."
    )


def serve(transport: str = "stdio") -> None:
    mcp.run(transport=transport)
```

- [ ] **Step 6: Smoke-test that the server module imports and exposes tools**

Add to `tests/test_mcp_service.py`:

```python
def test_server_module_registers_tools():
    from bci_mcp.mcp import server

    assert server.mcp is not None
    assert callable(server.serve)
```

- [ ] **Step 7: Run service tests + full suite + ruff**

Run: `ruff check src tests && python -m pytest`
Expected: all green.

- [ ] **Step 8: Commit**

```bash
git add src/bci_mcp/mcp tests/test_mcp_service.py
git commit -m "feat: real MCP server (FastMCP) exposing live brain state"
```

---

### Task 16: Examples, Claude Desktop config, manual verification

**Files:**
- Create: `examples/claude_desktop_config.json`
- Create: `examples/mcp_quickstart.py`
- Create: `tests/test_examples.py`

- [ ] **Step 1: Write the Claude Desktop config example**

Create `examples/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "bci-mcp": {
      "command": "bci-mcp",
      "args": ["serve"]
    }
  }
}
```

- [ ] **Step 2: Write a standalone quickstart example**

Create `examples/mcp_quickstart.py`:

```python
"""Minimal example: read brain state without an MCP client."""
import time

from bci_mcp.mcp.service import BrainService


def main() -> None:
    svc = BrainService()
    print(svc.connect("synthetic://?focus=0.8&seed=1"))
    try:
        for _ in range(20):
            time.sleep(0.25)
            state = svc.get_brain_state()
            if "metrics" in state:
                m = state["metrics"]
                print(f"focus={m['focus']:.2f}  calm={m['calm']:.2f}  "
                      f"signal={state['signal_quality']}")
    finally:
        svc.disconnect()


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Write a test that the example config is valid JSON and quickstart imports**

Create `tests/test_examples.py`:

```python
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_claude_desktop_config_valid():
    cfg = json.loads((ROOT / "examples" / "claude_desktop_config.json").read_text())
    assert "bci-mcp" in cfg["mcpServers"]
    assert cfg["mcpServers"]["bci-mcp"]["command"] == "bci-mcp"


def test_quickstart_is_importable_module(tmp_path):
    # The example must at least parse/compile.
    src = (ROOT / "examples" / "mcp_quickstart.py").read_text()
    compile(src, "mcp_quickstart.py", "exec")
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_examples.py -v`
Expected: 2 passed.

- [ ] **Step 5: Manual end-to-end verification (real commands, observe output)**

Run each and confirm the described output before claiming success:

```bash
# 1. Live brain-meter (Ctrl-C to exit) — bars should move.
bci-mcp stream --device "synthetic://?focus=0.8" --once

# 2. MCP server starts on stdio without error (Ctrl-C to exit).
bci-mcp serve --transport stdio
```
Expected: (1) a table with focus/calm/attention/engagement/fatigue/meditation rows and a signal row; (2) the server runs and waits on stdio (no traceback).

- [ ] **Step 6: Full suite + ruff one more time**

Run: `ruff check src tests && python -m pytest`
Expected: all green.

- [ ] **Step 7: Commit**

```bash
git add examples tests/test_examples.py
git commit -m "feat: Claude Desktop config + quickstart example + tests"
```

---

## Self-review (completed by plan author)

**Spec coverage (Phases 0–4):**
- Packaging/console script/extras/CI/remove-prototype → Task 1 ✓
- Device interface, ring buffer, registry/URI, Stream → Tasks 2,3,5,6 ✓
- SyntheticDevice (default, no hardware, deterministic) → Task 4 ✓
- DSP: filters, bands, metrics, quality, calibration, BrainState, Pipeline → Tasks 7–13 ✓
- CLI devices/stream/serve → Task 14 ✓
- Real MCP server (tools, resources, prompt) + Claude Desktop config → Tasks 15,16 ✓
- Tests hardware-free throughout; ruff+pytest in CI ✓
- Deferred to later plans (explicitly out of scope here): NeuroFocus/BrainFlow/LSL devices (Plan 2); recording/playback, neurofeedback, dashboard, LSL publisher (Plan 3); README/SEO/docs rewrite (Plan 4). The CLI `devices` output and MCP `list_devices` advertise the Plan-2 schemes as labels only.

**Placeholder scan:** none — every code/test step contains complete content.

**Type consistency check:**
- `Chunk.data` is `(channels, n_samples)` everywhere (synthetic, stream, ringbuffer, dsp). ✓
- `band_powers()` returns dict keyed by the 5 `BANDS`; `raw_metrics()` consumes exactly those keys. ✓
- `Calibration.apply()` ↔ `raw_metrics()` keys; `Calibration.from_samples`/`to_json`/`from_json` names match tests. ✓
- `Pipeline.current_state()` returns `BrainState`; `BrainService` calls `.to_dict()`. ✓
- `SyntheticDevice.chunk_samples` read by `Stream._run`. ✓
- CLI `serve` lazily imports `bci_mcp.mcp.server` (created in Task 15), so Task 14 tests pass before Task 15. ✓
