# BCI Features

## Device backends

BCI-MCP uses a URI-based device registry. Every backend implements the same `Device` ABC (`bci_mcp.core.device.Device`) and registers a URI scheme.

| Backend | URI prefix | Notes |
|---|---|---|
| **Synthetic** | `synthetic://` | No hardware; generates band-mixed EEG |
| **NeuroFocus v4** | `neurofocus://` | Serial (`neurofocus://serial/PORT`) or BLE (`neurofocus://ble/NAME`) |
| **BrainFlow** | `brainflow://` | OpenBCI Cyton, Ganglion, Muse 2/S, and more |
| **LSL** | `lsl://` | Any Lab Streaming Layer-compatible device |
| **Generic serial** | `serial://` | One integer sample per line at 115200 baud |
| **Playback** | `playback://` | Replay a recorded `.npz`, `.csv`, or `.edf` file |

The `Device` produces `Chunk` objects: `data` is `(channels, n_samples)` float32 in µV, `timestamps` is `(n_samples,)` in seconds.

## Acquisition architecture

```
Device.read() → Chunk → Stream → RingBuffer → consumers (Pipeline, Recorder, LSL publisher)
```

`Stream` runs in a background thread, calling `device.read()` at ~4× the chunk rate and feeding a `RingBuffer`. Consumers call `stream.latest(n)` to pull the most recent `n` samples.

## Recording and replay

Record to file:

```bash
bci-mcp record --device synthetic:// --seconds 60 --out session.npz
bci-mcp record --device synthetic:// --seconds 60 --out session.csv
bci-mcp record --device synthetic:// --seconds 60 --out session.edf   # needs [edf]
```

Replay:

```bash
bci-mcp play session.npz
```

The `PlaybackDevice` reads the recording at the original sample rate and loops (optional `?loop=true`).

## Neurofeedback trainer

```bash
bci-mcp neurofeedback --device synthetic:// --metric focus --target 0.7 --seconds 60
```

`NeurofeedbackSession` samples the pipeline at 4 Hz, tracks time in-zone (metric ≥ target), streak, and cumulative percentage. The session summary includes `time_in_zone_pct`, `mean_score`, and `best_streak`.

Available metrics: `focus`, `calm`, `attention`, `engagement`, `fatigue`, `meditation`.

## Web dashboard

```bash
bci-mcp dashboard --device synthetic:// --host 127.0.0.1 --port 8000
```

FastAPI + uvicorn serve a `/state` JSON endpoint and a live dashboard at `http://127.0.0.1:8000`. Requires the `[dashboard]` install extra.

## LSL publisher

The pipeline can publish its output to a Lab Streaming Layer outlet, making it compatible with the broader BCI ecosystem (OpenViBE, BCI2000, BCILAB, etc.). This is wired in via `bci_mcp.lsl.publisher`.

## Adding a device backend

1. Subclass `bci_mcp.core.device.Device`.
2. Implement `connect()`, `start()`, `read() → Chunk | None`, `stop()`, `disconnect()`.
3. Register: `from bci_mcp.core.registry import register; register("myscheme", factory_fn)`.

See `devices/synthetic.py` for the simplest example.