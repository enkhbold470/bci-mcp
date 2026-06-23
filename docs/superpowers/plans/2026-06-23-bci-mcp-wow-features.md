# BCI-MCP Plan 3 — Wow features

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development / executing-plans. Steps use checkbox (`- [ ]`).

**Goal:** Add the product wow-factor on top of the device-agnostic core: session recording + replay (CSV/npz/EDF), a neurofeedback "focus trainer", an LSL publisher for ecosystem interop, and a live web dashboard — all driven by the same `Pipeline`, all runnable with the synthetic brain.

**Architecture:** New consumers/adapters around the existing `Pipeline`/`Stream`/`BrainState`. A `Recorder` consumes the stream; a `PlaybackDevice` turns a saved recording back into a `Device` (closing the record→replay loop and making everything testable without hardware). The trainer, LSL publisher, and dashboard all read `BrainState` from a `Pipeline`. MCP and CLI gain the matching commands.

**Tech stack:** numpy, pyedflib (`[edf]`), pylsl (`[lsl]`), fastapi+uvicorn (`[dashboard]`), typer, rich.

**Builds on Plans 1–2.** Install: `python3 -m pip install -e ".[dev,devices,lsl,edf,dashboard]"`.

**Conventions:** source under `src/bci_mcp/`, tests under `tests/`, `python3 -m pytest`, `ruff check src tests`, **one commit per task, NO `Co-Authored-By` trailer in any commit message.** Optional-lib tests use `pytest.importorskip`.

---

### Task 1: Recording I/O (CSV + npz + EDF)

**Files:**
- Create: `src/bci_mcp/recording/__init__.py` (empty)
- Create: `src/bci_mcp/recording/writer.py`
- Create: `src/bci_mcp/recording/reader.py`
- Create: `tests/test_recording.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_recording.py`:

```python
import numpy as np
import pytest

from bci_mcp.recording.reader import load_recording
from bci_mcp.recording.writer import save_recording


@pytest.mark.parametrize("ext", ["npz", "csv"])
def test_roundtrip_npz_csv(tmp_path, ext):
    data = np.arange(12, dtype=np.float32).reshape(2, 6)
    path = str(tmp_path / f"rec.{ext}")
    out = save_recording(data, sample_rate=128.0, channel_names=["a", "b"], path=path,
                         metadata={"device": "synthetic"})
    rec = load_recording(out)
    assert rec.sample_rate == 128.0
    assert rec.channel_names == ["a", "b"]
    assert rec.data.shape == (2, 6)
    assert np.allclose(rec.data, data, atol=1e-4)


def test_format_inferred_from_extension(tmp_path):
    data = np.zeros((1, 4), dtype=np.float32)
    out = save_recording(data, 100.0, ["x"], str(tmp_path / "r.npz"))
    assert out.endswith(".npz")


def test_edf_roundtrip(tmp_path):
    pytest.importorskip("pyedflib")
    data = (np.random.default_rng(0).normal(0, 20, (2, 512))).astype(np.float32)
    path = str(tmp_path / "rec.edf")
    save_recording(data, 256.0, ["c3", "c4"], path)
    rec = load_recording(path)
    assert rec.data.shape[0] == 2
    assert rec.sample_rate == 256.0
    # EDF stores with finite precision; check correlation not exact equality
    assert np.corrcoef(rec.data[0], data[0])[0, 1] > 0.99
```

- [ ] **Step 2: Run, confirm fail** — ModuleNotFoundError.

- [ ] **Step 3: Implement reader**

Create `src/bci_mcp/recording/reader.py`:

```python
"""Load EEG recordings (CSV / npz / EDF) into a uniform Recording object."""
from __future__ import annotations

import json
from dataclasses import dataclass, field

import numpy as np


@dataclass
class Recording:
    data: np.ndarray  # (channels, n_samples), float32
    sample_rate: float
    channel_names: list[str]
    metadata: dict = field(default_factory=dict)


def load_recording(path: str) -> Recording:
    ext = path.rsplit(".", 1)[-1].lower()
    if ext == "npz":
        npz = np.load(path, allow_pickle=False)
        meta = json.loads(str(npz["metadata"])) if "metadata" in npz else {}
        return Recording(
            data=npz["data"].astype(np.float32),
            sample_rate=float(npz["sample_rate"]),
            channel_names=[str(c) for c in npz["channel_names"]],
            metadata=meta,
        )
    if ext == "csv":
        import csv

        with open(path, newline="") as f:
            reader = csv.reader(f)
            header = next(reader)
            channel_names = header[1:]  # first col is timestamp
            rows = [[float(x) for x in row] for row in reader]
        arr = np.array(rows, dtype=np.float32).T  # (cols, n)
        sample_rate = 0.0
        if arr.shape[1] > 1:
            dt = arr[0, 1] - arr[0, 0]
            sample_rate = 1.0 / dt if dt > 0 else 0.0
        return Recording(data=arr[1:, :], sample_rate=sample_rate,
                         channel_names=channel_names)
    if ext == "edf":
        import pyedflib

        reader = pyedflib.EdfReader(path)
        n = reader.signals_in_file
        names = [reader.getLabel(i) for i in range(n)]
        rate = reader.getSampleFrequency(0)
        data = np.vstack([reader.readSignal(i) for i in range(n)]).astype(np.float32)
        reader.close()
        return Recording(data=data, sample_rate=float(rate), channel_names=names)
    raise ValueError(f"Unsupported recording format: .{ext}")
```

- [ ] **Step 4: Implement writer**

Create `src/bci_mcp/recording/writer.py`:

```python
"""Save EEG data to CSV / npz / EDF."""
from __future__ import annotations

import json

import numpy as np


def save_recording(data: np.ndarray, sample_rate: float, channel_names: list[str],
                   path: str, fmt: str | None = None, metadata: dict | None = None) -> str:
    fmt = (fmt or path.rsplit(".", 1)[-1]).lower()
    metadata = metadata or {}
    if fmt == "npz":
        np.savez(path, data=data.astype(np.float32), sample_rate=float(sample_rate),
                 channel_names=np.array(channel_names), metadata=json.dumps(metadata))
    elif fmt == "csv":
        import csv

        n = data.shape[1]
        t = np.arange(n) / sample_rate if sample_rate else np.arange(n, dtype=float)
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", *channel_names])
            for i in range(n):
                writer.writerow([t[i], *data[:, i].tolist()])
    elif fmt == "edf":
        import pyedflib

        n_ch = data.shape[0]
        writer = pyedflib.EdfWriter(path, n_ch, file_type=pyedflib.FILETYPE_EDFPLUS)
        headers = []
        for i in range(n_ch):
            ch = data[i]
            headers.append({
                "label": channel_names[i], "dimension": "uV",
                "sample_frequency": float(sample_rate),
                "physical_min": float(min(ch.min(), -1.0)),
                "physical_max": float(max(ch.max(), 1.0)),
                "digital_min": -32768, "digital_max": 32767,
                "transducer": "", "prefilter": "",
            })
        writer.setSignalHeaders(headers)
        writer.writeSamples([data[i].astype(np.float64) for i in range(n_ch)])
        writer.close()
    else:
        raise ValueError(f"Unsupported recording format: {fmt}")
    return path
```

Note: verify the installed `pyedflib` API for `setSignalHeaders`/`writeSamples`/`sample_frequency` key (older versions use `sample_rate`); adapt if the EDF test fails, keeping the round-trip test green.

- [ ] **Step 5: Create `src/bci_mcp/recording/__init__.py`** (empty).

- [ ] **Step 6: Run, confirm pass** — `python3 -m pytest tests/test_recording.py -v` → 4 passed (EDF skips only if pyedflib missing).

- [ ] **Step 7: Commit** — `git add src/bci_mcp/recording tests/test_recording.py && git commit -m "feat: recording I/O (CSV, npz, EDF)"`

---

### Task 2: PlaybackDevice + Recorder + Pipeline.record

**Files:**
- Create: `src/bci_mcp/devices/playback.py`
- Modify: `src/bci_mcp/devices/__init__.py`
- Create: `src/bci_mcp/recording/recorder.py`
- Modify: `src/bci_mcp/pipeline.py` (add `record`)
- Create: `tests/test_playback.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_playback.py`:

```python
import time

import numpy as np

from bci_mcp.core.registry import create_device
from bci_mcp.devices.playback import PlaybackDevice
from bci_mcp.pipeline import Pipeline
from bci_mcp.recording.reader import Recording


def test_playback_replays_recording():
    data = np.arange(20, dtype=np.float32).reshape(1, 20)
    rec = Recording(data=data, sample_rate=100.0, channel_names=["ch1"])
    dev = PlaybackDevice(rec, chunk_samples=5)
    dev.connect()
    dev.start()
    collected = []
    for _ in range(20):
        c = dev.read()
        if c is not None:
            collected.append(c.data)
        else:
            break
        time.sleep(0.01)
    dev.stop()
    dev.disconnect()
    out = np.concatenate(collected, axis=1)
    assert np.allclose(out, data)


def test_record_then_playback_via_pipeline(tmp_path):
    path = str(tmp_path / "session.npz")
    p = Pipeline("synthetic://?seed=1")
    p.start()
    time.sleep(0.5)
    out = p.record(seconds=0.5, path=path)
    p.stop()
    assert out == path

    dev = create_device(f"playback://{path}")
    assert isinstance(dev, PlaybackDevice)
    assert dev.info.channel_count == 4
```

- [ ] **Step 2: Run, confirm fail** — ModuleNotFoundError.

- [ ] **Step 3: Implement Recorder**

Create `src/bci_mcp/recording/recorder.py`:

```python
"""A Stream consumer that accumulates chunks for later saving."""
from __future__ import annotations

import numpy as np

from ..core.device import Chunk


class Recorder:
    def __init__(self) -> None:
        self._chunks: list[np.ndarray] = []
        self._active = False

    def start(self) -> None:
        self._active = True

    def stop(self) -> None:
        self._active = False

    def __call__(self, chunk: Chunk) -> None:
        if self._active:
            self._chunks.append(chunk.data.copy())

    def data(self) -> np.ndarray:
        if not self._chunks:
            return np.zeros((0, 0), dtype=np.float32)
        return np.concatenate(self._chunks, axis=1)
```

- [ ] **Step 4: Implement PlaybackDevice**

Create `src/bci_mcp/devices/playback.py`:

```python
"""Replay a saved recording as a live Device."""
from __future__ import annotations

import numpy as np

from ..core.device import Chunk, Device, DeviceInfo
from ..core.registry import register
from ..recording.reader import Recording, load_recording


class PlaybackDevice(Device):
    def __init__(self, recording: Recording | str, chunk_samples: int = 32,
                 speed: float = 1.0, loop: bool = False, uri: str | None = None) -> None:
        rec = load_recording(recording) if isinstance(recording, str) else recording
        self._rec = rec
        self.chunk_samples = max(1, int(chunk_samples * max(speed, 1e-6)))
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
        recording=path, speed=float(params.get("speed", 1.0)),
        loop=params.get("loop", "false").lower() == "true", uri=parsed.geturl(),
    )


register("playback", _factory)
```

- [ ] **Step 5: Register on import** — add to `src/bci_mcp/devices/__init__.py`:

```python
from . import playback as _playback  # noqa: F401
```

- [ ] **Step 6: Add `record` to Pipeline** — append to `Pipeline` in `src/bci_mcp/pipeline.py`:

```python
    def record(self, seconds: float, path: str, fmt: str | None = None) -> str:
        from .recording.recorder import Recorder
        from .recording.writer import save_recording

        recorder = Recorder()
        self.stream.add_consumer(recorder)
        recorder.start()
        time.sleep(seconds)
        recorder.stop()
        data = recorder.data()
        return save_recording(
            data, self.device.info.sample_rate, self.device.info.channel_names, path, fmt,
            metadata={"device": self.device.info.name, "uri": self.device.info.uri},
        )
```

- [ ] **Step 7: Run, confirm pass** — `python3 -m pytest tests/test_playback.py -v` → 2 passed.

- [ ] **Step 8: Commit** — `git add src/bci_mcp/devices/playback.py src/bci_mcp/devices/__init__.py src/bci_mcp/recording/recorder.py src/bci_mcp/pipeline.py tests/test_playback.py && git commit -m "feat: PlaybackDevice + Recorder + Pipeline.record (record→replay loop)"`

---

### Task 3: Neurofeedback trainer

**Files:**
- Create: `src/bci_mcp/neurofeedback/__init__.py` (empty)
- Create: `src/bci_mcp/neurofeedback/trainer.py`
- Create: `tests/test_neurofeedback.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_neurofeedback.py`:

```python
from bci_mcp.neurofeedback.trainer import NeurofeedbackSession


class FakePipeline:
    """Feeds scripted metric values without threads."""

    def __init__(self, values):
        self._values = list(values)

    def current_state(self):
        from bci_mcp.dsp.state import BrainState

        if not self._values:
            return None
        v = self._values.pop(0)
        return BrainState(timestamp=0.0, metrics={"focus": v}, band_powers={},
                          relative_band_powers={}, signal_quality="good",
                          quality_score=1.0, artifacts=[], channels=1,
                          sample_rate=256.0, calibrated=False)


def test_score_counts_time_in_zone():
    pipe = FakePipeline([0.9, 0.2, 0.8, 0.85, 0.1])
    sess = NeurofeedbackSession(pipe, metric="focus", target=0.7)
    sess.start()
    for _ in range(5):
        sess.sample()
    summary = sess.summary()
    # 3 of 5 samples >= 0.7
    assert summary.samples == 5
    assert abs(summary.time_in_zone_pct - 60.0) < 1e-6
    assert 0.0 <= summary.mean_score <= 1.0


def test_score_dict_shape():
    pipe = FakePipeline([0.8])
    sess = NeurofeedbackSession(pipe, metric="focus", target=0.7)
    sess.start()
    sess.sample()
    score = sess.score()
    assert "in_zone" in score and "cumulative_in_zone_pct" in score
    assert score["in_zone"] is True
```

- [ ] **Step 2: Run, confirm fail** — ModuleNotFoundError.

- [ ] **Step 3: Implement**

Create `src/bci_mcp/neurofeedback/trainer.py`:

```python
"""Neurofeedback training session: reward time spent above a metric target."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NeurofeedbackSummary:
    metric: str
    target: float
    samples: int
    time_in_zone_pct: float
    mean_score: float
    best_streak: int


class NeurofeedbackSession:
    def __init__(self, pipeline, metric: str = "focus", target: float = 0.7) -> None:
        self.pipeline = pipeline
        self.metric = metric
        self.target = target
        self._values: list[float] = []
        self._in_zone = 0
        self._streak = 0
        self._best_streak = 0
        self._last_in_zone = False

    def start(self) -> None:
        self._values.clear()
        self._in_zone = 0
        self._streak = 0
        self._best_streak = 0
        self._last_in_zone = False

    def sample(self) -> float | None:
        state = self.pipeline.current_state()
        if state is None or self.metric not in state.metrics:
            return None
        value = float(state.metrics[self.metric])
        self._values.append(value)
        if value >= self.target:
            self._in_zone += 1
            self._streak += 1
            self._best_streak = max(self._best_streak, self._streak)
            self._last_in_zone = True
        else:
            self._streak = 0
            self._last_in_zone = False
        return value

    def score(self) -> dict:
        n = len(self._values)
        return {
            "metric": self.metric,
            "target": self.target,
            "current": self._values[-1] if self._values else None,
            "in_zone": self._last_in_zone,
            "cumulative_in_zone_pct": (100.0 * self._in_zone / n) if n else 0.0,
            "samples": n,
        }

    def summary(self) -> NeurofeedbackSummary:
        n = len(self._values)
        return NeurofeedbackSummary(
            metric=self.metric, target=self.target, samples=n,
            time_in_zone_pct=(100.0 * self._in_zone / n) if n else 0.0,
            mean_score=(sum(self._values) / n) if n else 0.0,
            best_streak=self._best_streak,
        )
```

- [ ] **Step 4: Create `src/bci_mcp/neurofeedback/__init__.py`** (empty).

- [ ] **Step 5: Run, confirm pass** — `python3 -m pytest tests/test_neurofeedback.py -v` → 2 passed.

- [ ] **Step 6: Commit** — `git add src/bci_mcp/neurofeedback tests/test_neurofeedback.py && git commit -m "feat: neurofeedback training session + scoring"`

---

### Task 4: LSL publisher

**Files:**
- Create: `src/bci_mcp/lsl/__init__.py` (empty)
- Create: `src/bci_mcp/lsl/publisher.py`
- Create: `tests/test_lsl_publisher.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_lsl_publisher.py`:

```python
import time

import pytest

pytest.importorskip("pylsl")

import numpy as np  # noqa: E402

from bci_mcp.lsl.publisher import LSLPublisher  # noqa: E402


def test_raw_publish_roundtrip():
    from pylsl import StreamInlet, resolve_byprop

    pub = LSLPublisher(name="BCITestOut", channel_names=["a", "b"], sample_rate=100.0)
    pub.open()
    time.sleep(0.2)
    streams = resolve_byprop("name", "BCITestOut", timeout=5.0)
    assert streams, "publisher stream not found"
    inlet = StreamInlet(streams[0])
    inlet.open_stream()
    for _ in range(20):
        pub.publish_chunk(np.array([[1.0], [2.0]], dtype=np.float32))
        time.sleep(0.005)
    sample = None
    for _ in range(20):
        sample, _ = inlet.pull_sample(timeout=0.0)
        if sample is not None:
            break
        time.sleep(0.05)
    inlet.close_stream()
    pub.close()
    assert sample is not None
    assert np.allclose(sample, [1.0, 2.0])
```

- [ ] **Step 2: Run, confirm fail** — ModuleNotFoundError.

- [ ] **Step 3: Implement**

Create `src/bci_mcp/lsl/publisher.py`. Verify the installed `pylsl` `StreamInfo`/`StreamOutlet`/`push_chunk`/`push_sample` API and adapt if needed.

```python
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
```

- [ ] **Step 4: Create `src/bci_mcp/lsl/__init__.py`** (empty).

- [ ] **Step 5: Run, confirm pass** (pylsl installed) — `python3 -m pytest tests/test_lsl_publisher.py -v` → 1 passed (or skip w/ reason).

- [ ] **Step 6: Commit** — `git add src/bci_mcp/lsl tests/test_lsl_publisher.py && git commit -m "feat: LSL publisher (raw + metrics outlets)"`

---

### Task 5: MCP + CLI wiring for record / neurofeedback

**Files:**
- Modify: `src/bci_mcp/mcp/service.py` (add `record`, `start_neurofeedback`, `get_neurofeedback_score`)
- Modify: `src/bci_mcp/mcp/server.py` (expose the three new tools)
- Modify: `src/bci_mcp/cli.py` (add `record`, `play`, `neurofeedback`)
- Modify: `tests/test_mcp_service.py` (cover new methods)
- Create: `tests/test_cli_record.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_mcp_service.py`:

```python
def test_record_and_neurofeedback(tmp_path):
    import time

    svc = BrainService()
    svc.connect("synthetic://?seed=1")
    try:
        time.sleep(0.5)
        out = svc.record(seconds=0.4, path=str(tmp_path / "s.npz"))
        assert out["path"].endswith(".npz")

        started = svc.start_neurofeedback(metric="focus", target=0.5)
        assert started["metric"] == "focus"
        time.sleep(0.4)
        for _ in range(5):
            time.sleep(0.1)
            score = svc.get_neurofeedback_score()
        assert "cumulative_in_zone_pct" in score
    finally:
        svc.disconnect()


def test_neurofeedback_requires_connection():
    svc = BrainService()
    assert "error" in svc.start_neurofeedback()
    assert "error" in svc.get_neurofeedback_score()
```

Create `tests/test_cli_record.py`:

```python
from typer.testing import CliRunner

from bci_mcp.cli import app

runner = CliRunner()


def test_record_and_play(tmp_path):
    path = str(tmp_path / "rec.npz")
    r1 = runner.invoke(app, ["record", "--device", "synthetic://?seed=1",
                             "--seconds", "0.4", "--out", path])
    assert r1.exit_code == 0
    r2 = runner.invoke(app, ["play", path, "--once"])
    assert r2.exit_code == 0
    assert "focus" in r2.stdout.lower()
```

- [ ] **Step 2: Run, confirm fail.**

- [ ] **Step 3: Implement service methods** — add to `BrainService` in `src/bci_mcp/mcp/service.py`:

```python
    def record(self, seconds: float = 10.0, path: str = "session.npz",
               fmt: str | None = None) -> dict:
        if self._pipeline is None:
            return {"error": "not connected"}
        out = self._pipeline.record(seconds=seconds, path=path, fmt=fmt)
        return {"recorded": True, "path": out, "seconds": seconds}

    def start_neurofeedback(self, metric: str = "focus", target: float = 0.7) -> dict:
        if self._pipeline is None:
            return {"error": "not connected"}
        from ..neurofeedback.trainer import NeurofeedbackSession

        self._nf = NeurofeedbackSession(self._pipeline, metric=metric, target=target)
        self._nf.start()
        return {"started": True, "metric": metric, "target": target}

    def get_neurofeedback_score(self) -> dict:
        nf = getattr(self, "_nf", None)
        if nf is None:
            return {"error": "no neurofeedback session — call start_neurofeedback first"}
        nf.sample()
        return nf.score()
```

Also add `self._nf = None` in `BrainService.__init__`.

- [ ] **Step 4: Expose MCP tools** — add to `src/bci_mcp/mcp/server.py`:

```python
@mcp.tool()
def record(seconds: float = 10.0, path: str = "session.npz", fmt: str | None = None) -> dict:
    """Record the live stream for N seconds to a file (npz/csv/edf)."""
    return _service.record(seconds, path, fmt)


@mcp.tool()
def start_neurofeedback(metric: str = "focus", target: float = 0.7) -> dict:
    """Begin a neurofeedback session rewarding time spent above a metric target."""
    return _service.start_neurofeedback(metric, target)


@mcp.tool()
def get_neurofeedback_score() -> dict:
    """Sample the current neurofeedback score (in-zone now + cumulative %)."""
    return _service.get_neurofeedback_score()
```

- [ ] **Step 5: Add CLI commands** — add to `src/bci_mcp/cli.py`:

```python
@app.command()
def record(device: str = typer.Option("synthetic://"), seconds: float = 10.0,
           out: str = "session.npz", fmt: str = typer.Option(None)) -> None:
    """Record a session to a file."""
    pipeline = Pipeline(device)
    pipeline.start()
    try:
        time.sleep(0.5)  # warm up
        path = pipeline.record(seconds=seconds, path=out, fmt=fmt)
        console.print(f"[green]Saved[/green] {path}")
    finally:
        pipeline.stop()


@app.command()
def play(path: str, once: bool = typer.Option(False)) -> None:
    """Replay a recording through the live brain-meter."""
    stream(device=f"playback://{path}", once=once)


@app.command()
def neurofeedback(device: str = typer.Option("synthetic://"),
                  metric: str = "focus", target: float = 0.7,
                  seconds: float = 30.0) -> None:
    """Run a neurofeedback session and print a summary."""
    from .neurofeedback.trainer import NeurofeedbackSession

    pipeline = Pipeline(device)
    pipeline.start()
    sess = NeurofeedbackSession(pipeline, metric=metric, target=target)
    sess.start()
    try:
        time.sleep(0.5)
        end = time.time() + seconds
        with Live(console=console, refresh_per_second=4) as live:
            while time.time() < end:
                time.sleep(0.25)
                sess.sample()
                s = sess.score()
                live.update(f"{metric}: {s['current']:.2f}  in-zone: "
                            f"{s['cumulative_in_zone_pct']:.0f}%")
        summary = sess.summary()
        console.print(f"[bold]Session:[/bold] {summary.time_in_zone_pct:.0f}% in zone, "
                      f"mean {summary.mean_score:.2f}, best streak {summary.best_streak}")
    except KeyboardInterrupt:
        pass
    finally:
        pipeline.stop()
```

Note: `play` calls `stream(...)`; ensure `stream` is defined above `play` in the file (it is, from Plan 1). The `Live` import is already at the top from Plan 1.

- [ ] **Step 6: Run, confirm pass** — `python3 -m pytest tests/test_mcp_service.py tests/test_cli_record.py -v` → all pass.

- [ ] **Step 7: Commit** — `git add src/bci_mcp tests && git commit -m "feat: MCP + CLI for record, play, neurofeedback"`

---

### Task 6: Web dashboard

**Files:**
- Create: `src/bci_mcp/dashboard/__init__.py` (empty)
- Create: `src/bci_mcp/dashboard/server.py`
- Create: `src/bci_mcp/dashboard/static/index.html`
- Modify: `src/bci_mcp/cli.py` (add `dashboard`)
- Create: `tests/test_dashboard.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_dashboard.py`:

```python
import time

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from bci_mcp.dashboard.server import create_app  # noqa: E402
from bci_mcp.pipeline import Pipeline  # noqa: E402


def test_dashboard_serves_html_and_state():
    pipeline = Pipeline("synthetic://?seed=1")
    pipeline.start()
    time.sleep(0.5)
    app = create_app(pipeline)
    client = TestClient(app)
    try:
        home = client.get("/")
        assert home.status_code == 200
        assert "BCI-MCP" in home.text

        state = client.get("/api/state")
        assert state.status_code == 200
        body = state.json()
        # warming_up dict or a full BrainState dict
        assert "metrics" in body or "status" in body
    finally:
        pipeline.stop()
```

- [ ] **Step 2: Run, confirm fail** — ModuleNotFoundError.

- [ ] **Step 3: Implement the server**

Create `src/bci_mcp/dashboard/server.py`. Verify the installed FastAPI API (`FastAPI`, `WebSocket`, `FileResponse`); adapt if needed.

```python
"""FastAPI dashboard exposing live brain state over REST + WebSocket."""
from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from ..pipeline import Pipeline

_STATIC = Path(__file__).parent / "static"


def create_app(pipeline: Pipeline) -> FastAPI:
    app = FastAPI(title="BCI-MCP Dashboard")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(_STATIC / "index.html")

    @app.get("/api/state")
    def state() -> dict:
        s = pipeline.current_state()
        return s.to_dict() if s is not None else {"status": "warming_up"}

    @app.websocket("/ws")
    async def ws(websocket: WebSocket) -> None:
        await websocket.accept()
        try:
            while True:
                s = pipeline.current_state()
                await websocket.send_json(s.to_dict() if s is not None
                                          else {"status": "warming_up"})
                await asyncio.sleep(0.25)
        except WebSocketDisconnect:
            pass

    return app


def serve_dashboard(device: str = "synthetic://", host: str = "127.0.0.1",
                    port: int = 8000) -> None:
    import uvicorn

    pipeline = Pipeline(device)
    pipeline.start()
    app = create_app(pipeline)
    try:
        uvicorn.run(app, host=host, port=port)
    finally:
        pipeline.stop()
```

- [ ] **Step 4: Implement the frontend**

Create `src/bci_mcp/dashboard/static/index.html` — a self-contained page (no build step) that polls `/api/state` and renders focus/calm gauges + band-power bars. Keep it visually clean (dark theme, large metric bars). Minimum viable content:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>BCI-MCP — Live Brain State</title>
<style>
  :root { color-scheme: dark; }
  body { font-family: ui-sans-serif, system-ui, sans-serif; background:#0b0e14; color:#e6e6e6;
         margin:0; padding:2rem; }
  h1 { font-weight:700; letter-spacing:-0.02em; }
  .sub { color:#8a93a6; margin-top:-0.5rem; }
  .metric { margin:1rem 0; }
  .metric .label { display:flex; justify-content:space-between; font-size:0.9rem; }
  .bar { height:14px; background:#1a2030; border-radius:7px; overflow:hidden; margin-top:4px; }
  .fill { height:100%; background:linear-gradient(90deg,#4f8cff,#9b6bff); width:0%;
          transition:width .2s ease; }
  .bands { display:flex; gap:8px; margin-top:1.5rem; align-items:flex-end; height:120px; }
  .band { flex:1; text-align:center; }
  .band .col { background:#2a3650; border-radius:4px 4px 0 0; transition:height .2s; }
  #signal { margin-top:1rem; font-size:0.9rem; }
</style>
</head>
<body>
  <h1>BCI-MCP</h1>
  <p class="sub">Live brain state · plug your brain into any AI</p>
  <div id="metrics"></div>
  <div class="bands" id="bands"></div>
  <div id="signal"></div>
<script>
const METRICS = ["focus","calm","attention","engagement","fatigue","meditation"];
const BANDS = ["delta","theta","alpha","beta","gamma"];
const mEl = document.getElementById("metrics");
mEl.innerHTML = METRICS.map(m =>
  `<div class="metric"><div class="label"><span>${m}</span><span id="v-${m}">–</span></div>
   <div class="bar"><div class="fill" id="f-${m}"></div></div></div>`).join("");
const bEl = document.getElementById("bands");
bEl.innerHTML = BANDS.map(b =>
  `<div class="band"><div class="col" id="b-${b}" style="height:2px"></div>${b}</div>`).join("");

async function tick(){
  try {
    const r = await fetch("/api/state"); const s = await r.json();
    if (s.metrics){
      for (const m of METRICS){
        const v = s.metrics[m] ?? 0;
        document.getElementById("v-"+m).textContent = v.toFixed(2);
        document.getElementById("f-"+m).style.width = (v*100)+"%";
      }
      const rel = s.relative_band_powers || {};
      const max = Math.max(0.001, ...BANDS.map(b => rel[b]||0));
      for (const b of BANDS)
        document.getElementById("b-"+b).style.height = (8 + 100*((rel[b]||0)/max))+"px";
      document.getElementById("signal").textContent =
        `signal: ${s.signal_quality} (${(s.quality_score||0).toFixed(2)})` +
        (s.artifacts && s.artifacts.length ? ` · ${s.artifacts.join(", ")}` : "");
    } else {
      document.getElementById("signal").textContent = "warming up…";
    }
  } catch(e){ /* keep polling */ }
}
setInterval(tick, 250); tick();
</script>
</body>
</html>
```

- [ ] **Step 5: Ensure the static dir ships** — confirm `pyproject.toml` `[tool.hatch.build.targets.wheel]` includes the package; add (if needed) so non-`.py` files are packaged:

```toml
[tool.hatch.build.targets.wheel.force-include]
"src/bci_mcp/dashboard/static" = "bci_mcp/dashboard/static"
```

Verify the editable install still finds `index.html` via the `Path(__file__).parent / "static"` lookup (it will in editable mode regardless).

- [ ] **Step 6: Add the CLI command** — add to `src/bci_mcp/cli.py`:

```python
@app.command()
def dashboard(device: str = typer.Option("synthetic://"), host: str = "127.0.0.1",
              port: int = 8000) -> None:
    """Launch the live web dashboard."""
    from .dashboard.server import serve_dashboard

    console.print(f"[green]Dashboard[/green] http://{host}:{port}  (device: {device})")
    serve_dashboard(device=device, host=host, port=port)
```

- [ ] **Step 7: Create `src/bci_mcp/dashboard/__init__.py`** (empty).

- [ ] **Step 8: Run, confirm pass** — `python3 -m pytest tests/test_dashboard.py -v` → 1 passed.

- [ ] **Step 9: Full suite + ruff** — `ruff check src tests && python3 -m pytest` → green (skips allowed for optional libs; note them).

- [ ] **Step 10: Commit** — `git add src/bci_mcp/dashboard src/bci_mcp/cli.py pyproject.toml tests/test_dashboard.py && git commit -m "feat: live web dashboard (FastAPI + WebSocket + SPA)"`

---

## Self-review (plan author)

**Spec coverage:** recording CSV/npz/EDF (Task 1) ✓; PlaybackDevice + record→replay loop (Task 2) ✓; neurofeedback trainer (Task 3) ✓; LSL publisher (Task 4) ✓; MCP+CLI record/play/neurofeedback (Task 5) ✓; web dashboard (Task 6) ✓.

**Hardware-free testing:** recording round-trips on disk; playback replays in memory; neurofeedback uses a scripted FakePipeline (deterministic, no threads); LSL publisher uses in-process inlet round-trip; dashboard uses FastAPI TestClient; MCP/CLI use the synthetic device. EDF/LSL/dashboard tests `importorskip` their optional libs.

**Type consistency:** `save_recording`/`load_recording`↔`Recording(data,sample_rate,channel_names,metadata)`; `PlaybackDevice` emits the standard `Chunk` and registers `playback://`; `Pipeline.record` returns the path; `BrainService.record/start_neurofeedback/get_neurofeedback_score` return dicts and are mirrored as MCP tools; `NeurofeedbackSession.score()` keys (`in_zone`, `cumulative_in_zone_pct`, `current`) match the dashboard/CLI/tests; dashboard `create_app(pipeline)` returns a FastAPI app with `/`, `/api/state`, `/ws`.

**Adaptation guards:** pyedflib/pylsl/fastapi imported lazily; tests skip when their libs/native deps are absent; implementers told to verify each library's installed API and adapt.
