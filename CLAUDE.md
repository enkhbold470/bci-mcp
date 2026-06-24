# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Git commits

**Never add `Co-authored-by` trailers** (Cursor, Claude, or any AI). See [AGENTS.md](AGENTS.md). Verify with `git log -1 --format='%B'` before pushing.

## What this project is

**BCI-MCP** is a Python package (`src/bci_mcp/`) that provides:

- **Device-agnostic EEG acquisition** via a URI registry (synthetic, NeuroFocus serial+BLE, BrainFlow/OpenBCI/Muse, LSL, generic serial, recording playback).
- **A real MCP server** built on the official MCP Python SDK (`mcp` on PyPI, `FastMCP`), exposing live brain state to Claude Desktop and any MCP client over stdio.
- **A DSP pipeline** that turns raw EEG into `BrainState` (focus, calm, attention, engagement, fatigue, meditation + δθαβγ band powers + signal quality).
- **A Rich CLI** with commands: `devices`, `stream`, `record`, `play`, `neurofeedback`, `dashboard`, `serve`.
- **Recording** (CSV/npz/EDF) + replay, neurofeedback trainer, LSL publisher, FastAPI web dashboard.

## Package layout

```
src/bci_mcp/
├── __init__.py            # triggers device registration; __version__ = "0.1.0"
├── cli.py                 # Typer CLI (entry point: bci-mcp)
├── pipeline.py            # Pipeline: Device → Stream → DSP → BrainState
├── core/
│   ├── device.py          # Device ABC, Chunk, DeviceInfo dataclasses
│   ├── registry.py        # URI registry (register/create_device/discover)
│   ├── ringbuffer.py      # RingBuffer
│   └── stream.py          # Stream (background thread polling device.read())
├── devices/
│   ├── synthetic.py       # SyntheticDevice — no hardware needed
│   ├── neurofocus.py      # NeuroFocus v4 (serial + BLE)
│   ├── brainflow_device.py # BrainFlow (OpenBCI, Muse, ...)
│   ├── lsl_device.py      # LSL consumer
│   ├── serial_device.py   # Generic serial (1 int/line)
│   └── playback.py        # PlaybackDevice (npz/csv/edf replay)
├── dsp/
│   ├── filters.py         # bandpass + notch (zero-phase, scipy.signal.filtfilt)
│   ├── bands.py           # band_powers() via Welch PSD, relative_band_powers()
│   ├── metrics.py         # raw_metrics() — focus/calm/attention/engagement/fatigue/meditation
│   ├── state.py           # BrainState dataclass
│   ├── quality.py         # assess_quality() — signal score + artifact flags
│   └── calibration.py     # Calibration — personalized min/max scaling
├── mcp/
│   ├── server.py          # FastMCP tools/resources/prompt + serve()
│   └── service.py         # BrainService — testable core (server.py wraps this)
├── recording/
│   ├── recorder.py        # Recorder stream consumer
│   ├── writer.py          # save_recording() — npz/csv/edf
│   └── reader.py          # load_recording() → Recording dataclass
├── neurofeedback/
│   └── trainer.py         # NeurofeedbackSession
├── lsl/
│   └── publisher.py       # LSL outlet publisher
└── dashboard/
    └── server.py          # FastAPI web dashboard
```

## Install and run

```bash
pip install -e ".[all,dev]"          # all extras + dev tools

bci-mcp devices                      # list URI schemes + discovered hardware
bci-mcp stream --device synthetic:// # live terminal brain-meter
bci-mcp stream --device synthetic:// --once   # single snapshot (good for CI smoke)
bci-mcp record --device synthetic:// --seconds 10 --out session.npz
bci-mcp play session.npz
bci-mcp serve                        # MCP server (stdio)
```

## Tests

```bash
ruff check src tests       # linter (must be clean before commit)
python -m pytest           # runs all tests (80+ hardware-free tests)
```

All tests are **hardware-free**: synthetic device, recording playback, in-process LSL, BrainFlow synthetic board. No EEG headset needed.

## Architecture

```
Device.read() → Chunk → Stream (background thread) → RingBuffer
                                                          │
Pipeline.current_state() pulls latest N samples, runs:   │
  filters.bandpass + filters.notch                        │
  → bands.band_powers (Welch PSD)                         │
  → metrics.raw_metrics                                   │
  → calibration.apply → BrainState                        │
                                                          │
Consumers: CLI brain-meter, FastMCP server, FastAPI dashboard,
           Recorder (→ npz/csv/edf), LSL publisher, NeurofeedbackSession
```

## Device URI registry

Every device backend calls `bci_mcp.core.registry.register(scheme, factory)` at import time. `create_device(uri)` parses the URI and calls the factory. Schemes: `synthetic`, `neurofocus`, `brainflow`, `lsl`, `serial`, `playback`.

## MCP server

`bci_mcp.mcp.server` uses `FastMCP` from the official MCP Python SDK. It runs over **stdio** (the standard for Claude Desktop). Tools: `list_devices`, `connect`, `disconnect`, `get_brain_state`, `get_band_powers`, `get_signal_quality`, `calibrate`, `record`, `start_neurofeedback`, `get_neurofeedback_score`, `mark_event`, `stream_summary`. Resources: `brain://state`, `brain://device`. Prompt: `interpret_brain_state`.

## Design docs

Specs and implementation plans live under `docs/superpowers/`.
