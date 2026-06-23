# BCI-MCP — "Plug your brain into any AI"

**Status:** Approved design (2026-06-23)
**Author:** brainstormed with jtsato@stanford.edu
**Repo:** `bci-mcp` (name kept for SEO) · Python package: `bci_mcp`

---

## 1. Summary

BCI-MCP is a **real [Model Context Protocol](https://modelcontextprotocol.io) server** that streams **live brain state** (focus, calm, attention, band powers, signal quality) from **any EEG device** — or a built-in **synthetic brain** that needs no hardware — into **Claude Desktop and any MCP client**. Around that headline feature it ships a device-agnostic toolkit: a live terminal brain-meter, a web dashboard, neurofeedback training, session recording/replay, and Lab Streaming Layer (LSL) interop.

This replaces the current prototype, which is a custom WebSocket/JSON-RPC API with a **verified import bug** (`server.py` uses `from ..bci...`, a relative import beyond the top-level package, so `python src/main.py` crashes on import for *every* invocation). The legacy WebSocket/JSON-RPC server is **dropped**; the MCP server (stdio + SSE) is the only network surface.

### Goals

- **"Any EEG device" is true, not aspirational** — synthetic, the user's NeuroFocus v4, OpenBCI, Muse, and anything on LSL, through one `Device` interface.
- **Zero-hardware demo always works** — synthetic brain + recording playback mean `pip install` → working demo → green CI, with no headset.
- **A genuinely novel, demoable killer feature** — Claude (or any MCP client) reading and reasoning about your live brain state.
- **A star-worthy, SEO/LLM-discoverable repo** — killer README, packaging metadata, examples, honest docs.

### Non-goals

- Medical-grade or diagnostic use (explicit disclaimer in docs).
- Inventing new EEG hardware/firmware (we *consume* the NeuroFocus firmware as-is).
- Reimplementing device drivers that BrainFlow already provides.

---

## 2. Architecture decision

**Chosen: BrainFlow-first acquisition behind a thin in-house `Device` interface, plus a custom NeuroFocus adapter and an LSL device.**

- [BrainFlow](https://brainflow.org) is the acquisition engine for OpenBCI / Muse / Neurosity / g.tec / etc. and provides a synthetic board and DSP helpers.
- Our own small `Device` ABC wraps it so MCP/CLI/DSP never depend on BrainFlow specifics, and so non-BrainFlow devices (NeuroFocus, LSL, generic serial, playback) plug into the same pipeline.
- A custom `NeuroFocusDevice` speaks the user's firmware protocol directly (serial + BLE).

Rejected alternatives: all-custom drivers (huge fragile surface; "any device" becomes a lie); LSL-only (forces users to run a separate per-device bridge; poor out-of-box UX — we *include* LSL but never *require* it).

---

## 3. Package layout

```
bci-mcp/
├── pyproject.toml                 # packaging, console scripts, deps + extras, keywords, classifiers
├── README.md                      # killer SEO README (hero GIF, badges, device table, quickstart)
├── CITATION.cff, CONTRIBUTING.md, CHANGELOG.md, LICENSE
├── src/bci_mcp/
│   ├── __init__.py                # version, top-level exports
│   ├── core/
│   │   ├── device.py              # Device ABC, DeviceInfo, Chunk types
│   │   ├── registry.py            # create_device(uri), list_devices(), URI parsing
│   │   ├── ringbuffer.py          # multi-channel numpy circular buffer
│   │   └── stream.py              # Stream: producer thread → fan-out to consumers
│   ├── devices/
│   │   ├── synthetic.py           # SyntheticDevice (default, no hardware)
│   │   ├── brainflow_device.py    # BrainFlowDevice (OpenBCI, Muse, many boards)
│   │   ├── neurofocus.py          # NeuroFocusDevice (serial + BLE)
│   │   ├── lsl_device.py          # LSLDevice (consume any LSL stream)
│   │   └── playback.py            # PlaybackDevice (replay a recording as a live device)
│   ├── dsp/
│   │   ├── filters.py             # bandpass, notch, detrend (scipy)
│   │   ├── bands.py               # Welch PSD → band powers (δ θ α β γ)
│   │   ├── metrics.py             # focus, calm, attention, engagement, fatigue (0..1)
│   │   ├── quality.py             # lead-off/railing/flatline/line-noise + artifacts
│   │   ├── calibration.py         # baseline capture → personalized metric scaling
│   │   └── state.py               # BrainState dataclass + serialization
│   ├── pipeline.py                # Stream → DSP → rolling BrainState
│   ├── recording/{writer.py,reader.py}   # CSV / npz / EDF
│   ├── neurofeedback/trainer.py   # focus-trainer loop + scoring
│   ├── lsl/publisher.py           # publish raw + metrics to LSL outlets
│   ├── mcp/server.py              # REAL MCP server (FastMCP): tools/resources/prompts
│   ├── dashboard/
│   │   ├── server.py              # FastAPI + WebSocket
│   │   └── static/                # single-page dashboard (gauges, band bars, trace)
│   └── cli.py                     # Typer CLI: devices/stream/record/play/serve/dashboard/neurofeedback
├── examples/
│   ├── claude_desktop_config.json
│   ├── mcp_quickstart.py
│   └── record_and_analyze.py
├── tests/                         # pytest, all hardware-free
├── docs/                          # MkDocs, rewritten to match reality
└── .github/workflows/{ci.yml,docs.yml}
```

The current `src/main.py`, `src/bci/`, `src/mcp/` are **removed**. Salvaged ideas: the scipy bandpass+notch filtering and the z-score event detection fold into `dsp/`.

---

## 4. Core abstractions

### `DeviceInfo`
`name: str`, `uri: str`, `sample_rate: float` (Hz), `channel_count: int`, `channel_names: list[str]`, `units: Literal["uV","counts"]`, `extra: dict`.

### `Chunk`
`data: np.ndarray` shape `(channels, n_samples)` `float32` in µV; `timestamps: np.ndarray` shape `(n_samples,)` (monotonic seconds).

### `Device` (ABC)
```python
class Device(ABC):
    info: DeviceInfo
    def connect(self) -> None: ...
    def start(self) -> None: ...        # begin streaming
    def read(self) -> Chunk | None: ... # non-blocking pull of new samples
    def stop(self) -> None: ...
    def disconnect(self) -> None: ...
    # also: __enter__/__exit__
```
Each device runs its own acquisition thread internally and exposes `read()`. The `Stream` (single producer) drains `read()` into the ring buffer and fans out to consumers (DSP pipeline, recorder, LSL publisher, dashboard, MCP). Multiple consumers, one producer — no consumer can stall acquisition.

### URI registry (the "any device" front door)
`create_device(uri: str) -> Device`, `list_devices() -> list[DeviceInfo]` (enumerate serial ports, BLE scan via bleak, BrainFlow boards, LSL streams).

| URI | Device |
|---|---|
| `synthetic://?channels=4&focus=0.7&seed=1` | SyntheticDevice (default) |
| `neurofocus://serial/<port>?baud=115200&format=ascii` | NeuroFocus over USB-serial |
| `neurofocus://ble/<name>` (default name `NEUROFOCUS_V4_01`) | NeuroFocus over BLE |
| `brainflow://synthetic`, `brainflow://cyton?serial_port=...`, `brainflow://muse_s`, `brainflow://ganglion?...` | BrainFlow boards |
| `lsl://<stream-name-or-type>` | any LSL stream |
| `playback://<path>?speed=1.0` | replay a recording |
| `serial://<port>?baud=115200` | generic one-int-per-line (covers the original firmware) |

---

## 5. NeuroFocus v4 device (first-class, from firmware docs)

Source: `~/Desktop/neurofocus/firmware/v4` `CODEBASE_MEMORY.md`, `TRANSPORT_AND_TOOLS.md`, `SIGNAL_CALCULATIONS.md`.

- **Channels:** 1. **Sample rate:** ~600 SPS (firmware DR_LVL_5; `SIGNAL_CALCULATIONS.md` mentions 660 SPS turbo — treat as a declared/configurable constant, default 600).
- **Serial (USB-CDC, 115200 baud):** ASCII signed decimal integer per line = raw signed 24-bit ADC counts. Commands: `b`=start, `s`=stop, `v`=reset.
- **BLE GATT:**
  - Device name `NEUROFOCUS_V4_01` (suffix varies per board).
  - Service `0338ff7c-6251-4029-a5d5-24e4fa856c8d`.
  - Data char (NOTIFY) `ad615f2b-cc93-4155-9e4d-f5f32cb9a2d7`.
  - Command char (WRITE) `b5e3d1c9-8a2f-4e7b-9c6d-1a3f5e7b9c2d`.
  - **ASCII mode (default):** one notification per sample, payload = ASCII decimal string.
  - **Binary-batch mode:** magic `0xE7 0x1E`, `seq` uint16-LE, `n` uint8 (default 8), then `n` × int32-LE raw counts. The adapter auto-detects ASCII vs binary by inspecting the first bytes (magic prefix).
  - Connecting auto-starts streaming; we still send `b`/`s` explicitly for determinism.
- **Counts → µV:** output µV = `count × 0.393`; scalp µV = output µV ÷ 100 (AD8422 instrumentation-amp gain). Constants live in `NeuroFocusDevice` as `LSB_UV = 3.3 / 8_388_608 * 1e6` (≈0.3933) and `AMP_GAIN = 100.0`; the device reports `units="uV"` (scalp-referred) after conversion.
- **Implementation:** serial backend uses `pyserial`; BLE backend uses `bleak` (async loop in the device's own thread). Both normalize to the same `Chunk` (µV). Reuses the proven parsing approach from the firmware's own `scripts/ble_eeg_receiver.py`.

---

## 6. DSP and the `BrainState`

### Pipeline
`Stream` → sliding analysis window (default 1.0 s, 4× overlap) → filter → band powers → metrics + quality → `BrainState`, published at ~4 Hz.

### Filters (`dsp/filters.py`)
Butterworth bandpass (default 1–45 Hz) + notch (50 or 60 Hz, configurable; NeuroFocus already does 50/60 in hardware). Zero-phase `filtfilt` for analysis windows.

### Band powers (`dsp/bands.py`)
Welch PSD per channel, integrated over: delta 1–4, theta 4–8, alpha 8–13, beta 13–30, gamma 30–45 Hz. Outputs absolute (µV²) and relative (fraction of total) power, channel-averaged and per-channel.

### Metrics (`dsp/metrics.py`) — all clamped 0..1
Documented heuristics, each scaled against a calibration baseline (§calibration):
- **focus / engagement** = `beta / (alpha + theta)`
- **calm / relaxation** = `alpha / (alpha + beta)`
- **attention** = `beta / theta`
- **fatigue / drowsiness** = `(theta + delta) / (alpha + beta)`
- **meditation** = `theta` (relative), as a secondary metric

Raw ratios are mapped to 0..1 via the baseline (min–max or z-score → logistic). Without calibration, sensible global defaults are used and `BrainState.calibrated=False`.

### Signal quality (`dsp/quality.py`)
`quality_score` 0..1 and label `good|fair|poor|no_contact` from: railing (near ±full-scale), flatline (variance ≈ 0), implausible amplitude, and line-noise ratio (50/60 Hz power vs neighbors). Artifact flags: `blink` (large frontal low-freq deflection), `jaw_clench` (broadband EMG burst), `railing`.

### Calibration (`dsp/calibration.py`)
Capture an N-second baseline (e.g. `relax` eyes-open or eyes-closed); store per-metric reference stats so 0..1 values are personalized. Persisted to a small JSON so it survives restarts.

### `BrainState` (`dsp/state.py`)
```python
@dataclass
class BrainState:
    timestamp: float
    metrics: dict[str, float]              # focus, calm, attention, engagement, fatigue, meditation (0..1)
    band_powers: dict[str, float]          # absolute µV², channel-averaged
    relative_band_powers: dict[str, float] # fractions summing ~1
    signal_quality: str                    # good|fair|poor|no_contact
    quality_score: float
    artifacts: list[str]
    channels: int
    sample_rate: float
    calibrated: bool
    def to_dict(self) -> dict: ...
    def summary(self) -> str: ...          # one-line human/LLM-friendly text
```

---

## 7. MCP server (the killer feature)

Built on the official `mcp` Python SDK (`FastMCP`). Transports: **stdio** (Claude Desktop) and optional **SSE/HTTP**. The server owns a single `Pipeline` and reflects whatever device is connected.

**Tools**
- `list_devices()` → available device URIs + info
- `connect(device_uri="synthetic://")` → connect + start pipeline
- `disconnect()`
- `get_brain_state()` → current `BrainState` (the money tool)
- `get_band_powers()` → absolute + relative band powers
- `get_signal_quality()` → quality score/label/artifacts
- `calibrate(seconds=20, condition="relax")` → set personalized baseline
- `record(seconds, path, format="edf")` → save a session
- `start_neurofeedback(metric="focus", target=0.7, seconds=60)` → begin a session
- `get_neurofeedback_score()` → live + cumulative score
- `mark_event(label)` → annotate the stream
- `stream_summary(seconds=30)` → window stats (mean focus, time-in-flow, peaks)

**Resources:** `brain://state`, `brain://session`, `brain://device`.
**Prompt:** `interpret_brain_state` (template that asks the model to interpret the live snapshot).

Ships with `examples/claude_desktop_config.json` and a `bci-mcp serve` (alias `bci-mcp mcp`) command that runs the stdio server.

---

## 8. CLI (`bci-mcp`, via console_scripts)

- `bci-mcp devices` — discover devices (serial/BLE/BrainFlow/LSL)
- `bci-mcp stream [--device URI]` — live Rich terminal brain-meter (the hero GIF)
- `bci-mcp record --device URI --seconds N --out FILE [--format edf|csv|npz]`
- `bci-mcp play FILE [--speed X]` — replay a recording through the full pipeline
- `bci-mcp serve` / `bci-mcp mcp` — start the MCP stdio server
- `bci-mcp dashboard [--device URI] [--port 8000]` — web dashboard
- `bci-mcp neurofeedback --metric focus [--target 0.7] [--seconds 120]`

---

## 9. Recording / playback, neurofeedback, LSL, dashboard

- **Recording:** `writer.py` → CSV, npz, and **EDF** (via `pyedflib`, optional `[edf]` extra) with metadata (device, sample rate, channels, calibration, event markers). `reader.py` loads any of them; `PlaybackDevice` replays as a live device (powers demos + CI without hardware).
- **Neurofeedback trainer:** session loop on a chosen metric with real-time score, terminal/visual reward, and a summary (time-in-zone, mean, best streak, improvement vs baseline). Exposed via CLI and MCP.
- **LSL publisher:** `pylsl` outlets for raw EEG and/or computed metrics so data interops with the BCI ecosystem (OpenViBE, BCILAB, timeflux). Optional `[lsl]` extra.
- **Dashboard:** FastAPI server + WebSocket pushing `BrainState` + a downsampled raw trace; single-page frontend with focus/calm gauges, live band-power bars, raw trace, and a signal-quality indicator. Detailed visual design is deferred to implementation (may use the frontend-design skill then).

---

## 10. Dependencies & install ergonomics

- **Core (always):** `numpy`, `scipy`, `mcp`, `rich`, `typer`. Keeps the **synthetic + MCP path installable everywhere**.
- **Extras:** `[devices]` = brainflow, bleak, pyserial · `[dashboard]` = fastapi, uvicorn, websockets · `[lsl]` = pylsl · `[edf]` = pyedflib · `[all]` = everything.
- `pip install bci-mcp` then `bci-mcp stream` works with the synthetic brain immediately.

---

## 11. Testing & CI

All tests are **hardware-free** (synthetic device + playback):
- DSP: a synthetic sine at a known frequency yields band power in the correct band; broadband noise spreads as expected.
- Metrics: monotonicity (more beta ⇒ higher focus), clamped to 0..1, calibration shifts scaling.
- Registry: every URI scheme parses to the right device with the right params; bad URIs raise clearly.
- Devices: synthetic emits correct shape/rate/units; NeuroFocus parser decodes ASCII and binary-batch frames from captured byte fixtures; counts→µV math.
- Recording round-trip: write → read → playback reproduces samples and metadata.
- MCP: drive tools/resources via an in-process MCP client; `get_brain_state` returns a valid `BrainState`.
- Quality: railing/flatline/blink fixtures classify correctly.

CI (`.github/workflows/ci.yml`): matrix Python 3.10–3.12, `ruff` lint + `pytest`. Existing docs deploy stays (consolidate the three redundant docs workflows into one).

---

## 12. Repo polish — SEO, stars, LLM-discoverability

- **README:** hero GIF (terminal meter + dashboard), one-line pitch, badges (PyPI, CI, license, stars, Python versions), **"Works with any EEG device" table** (synthetic / OpenBCI / Muse / NeuroFocus / LSL / generic serial), 30-second quickstart, **Claude Desktop config snippet**, architecture diagram, and a keyword-rich intro paragraph for search/LLM discovery: *EEG, BCI, brain-computer interface, MCP, Model Context Protocol, Claude, AI, neurofeedback, OpenBCI, Muse, BrainFlow, LSL, brainwave, neurotech, neuroscience, Python*.
- **Packaging:** `pyproject.toml` `keywords` + trove `classifiers`; accurate `description`/`urls`.
- **Discoverability:** a `gh repo edit --add-topic ...` command (and doc) to set GitHub topics; social-preview image suggestion; `CITATION.cff`.
- **Examples:** Claude Desktop config, MCP quickstart, record-and-analyze.
- **Docs:** rewrite the MkDocs site to match reality — **delete the current fictional API pages** (`BciDevice`, `McpClient`, etc. that don't exist) and wire `mkdocstrings` to the real `bci_mcp` package.
- **Disclaimer:** not a medical device; research/educational use.

---

## 13. Delivery phases

| # | Phase | Output |
|---|---|---|
| 0 | Packaging skeleton | `pyproject.toml`, `bci_mcp` package, ruff, pytest harness, CI; remove old `src/`; import bug gone |
| 1 | Core | `Device`, registry, ring buffer, `Stream` + `SyntheticDevice` + tests |
| 2 | DSP | filters, bands, metrics, quality, calibration, `BrainState`, `Pipeline` + tests |
| 3 | CLI brain-meter | `bci-mcp devices/stream` (Rich live view) |
| 4 | **MCP server** | FastMCP stdio/SSE, tools/resources/prompt, Claude Desktop docs + tests |
| 5 | NeuroFocus device | serial + BLE backends + generic `serial://` + byte-fixture tests |
| 6 | BrainFlow + LSL devices | OpenBCI/Muse/… + `lsl://` |
| 7 | Recording/playback | CSV/npz/EDF writer+reader, `PlaybackDevice` + round-trip tests |
| 8 | Neurofeedback | trainer loop + scoring (CLI + MCP) |
| 9 | Dashboard | FastAPI + WS + single-page UI |
| 10 | LSL publisher | raw + metrics outlets |
| 11 | Polish | killer README/SEO, MkDocs rewrite, examples, repo metadata |

Each phase is independently testable; phases 0–4 deliver the complete "plug your brain into AI" story on their own (synthetic + MCP), and later phases broaden hardware and add the wow features.
