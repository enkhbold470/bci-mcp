# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project actually is

A small Python application that reads a **single-channel EEG signal from a serial device**, filters it in real time, detects "neural events" by z-score thresholding, and optionally exposes that functionality over a **JSON-RPC 2.0 WebSocket API**. The repo is dominated by documentation (an MkDocs site under `docs/` plus a hand-written static site under `docs-static/`); the implementation is just three source files.

The entire implementation lives in:
- `src/bci/brain_interface.py` — the `BrainInterface` class (all signal acquisition, filtering, event detection, recording, plotting) plus `list_serial_ports()`. This is the core; everything else wraps it.
- `src/mcp/server.py` — a WebSocket + JSON-RPC server that wraps a single global `BrainInterface` instance and exposes it as `get_resource_*` and `invoke_tool_*` methods.
- `src/main.py` — the CLI entry point and an interactive text-menu console.

> **"MCP" here is a misnomer.** This does **not** use the official Model Context Protocol SDK (`mcp` on PyPI) or its stdio/SSE transports. It is a bespoke JSON-RPC-over-WebSocket API (via the `jsonrpcserver` library) that borrows MCP's "resources" and "tools" vocabulary. Do not assume `modelcontextprotocol`-SDK behavior. The local package directory `src/mcp/` shadows that PyPI package name.

## Running it

There is no installed console script; everything is launched via `src/main.py` **from the repo root** (this puts `src/` on `sys.path`, which the absolute imports in `main.py` rely on):

```bash
python src/main.py --server          # start the JSON-RPC WebSocket server on ws://0.0.0.0:8765
python src/main.py --interactive     # interactive text-menu console (also the default with no args)
python src/main.py --list-ports      # list available serial ports
python src/main.py --port <PORT> --record 60 [--plot] [--format npz|csv|pkl]
python src/main.py --port <PORT> --calibrate [--calibrate-duration 10]
```

Recordings are written to `./recordings/` (created automatically; git-ignored, as are `*.npz`, `*.csv`, `*.pkl`, `*.log`).

### Docker

```bash
docker-compose up -d      # bci-mcp-server (ws://localhost:8765) + docs (mkdocs serve on http://localhost:8000)
```

## ⚠️ Known issue: the app does not import as written (verify before assuming it runs)

`main.py` uses **absolute** imports (`from bci.brain_interface import ...`, `from mcp.server import run_server`) which require `src/` on the path. But `src/mcp/server.py` uses a **relative** import (`from ..bci.brain_interface import ...`). When launched the documented way (`python src/main.py`, with `src/` as the path root), `mcp` is a top-level package, so `..bci` raises:

```
ImportError: attempted relative import beyond top-level package
```

Because `main.py` imports `mcp.server` unconditionally at module top, this affects **every** invocation, not just `--server` (verified with an isolated reproduction of the package layout). The fix is to make the import style consistent — e.g. change `server.py` to `from bci.brain_interface import ...`. If you touch the run path, test an actual launch rather than trusting the docs.

There are additional latent runtime bugs in `server.py` (e.g. `get_resource_brain_signals` reads `brain_interface.BUFFER_SIZE` as an instance attribute, but `BUFFER_SIZE` is a module-level constant). Treat the server path as unverified.

## ⚠️ The documentation is aspirational, not descriptive

`docs/api/bci-module.md` and `docs/api/mcp-module.md` describe classes that **do not exist in the code** (`BciDevice`, `OpenBciDevice`, `EmotivDevice`, `McpClient`, `McpResponse`, `BciContextProcessor`, `FeatureExtractor`, …). The real code has exactly one device class (`BrainInterface`) and a flat set of JSON-RPC methods. Although `mkdocs.yml` configures the `mkdocstrings` plugin, the API pages are **hand-written stubs** (function bodies are `pass`) and contain **no autodoc directives**, so nothing is generated from source. When reasoning about behavior, read `src/`, not `docs/`. `docs/getting-started/quick-start.md` does accurately reflect the real CLI flags and JSON-RPC method names.

`docs/contributing.md` also references files/tooling that don't exist in the repo (`requirements-dev.txt`, `pre-commit` config).

## Tests

`pytest` and `pytest-cov` are in `requirements.txt` and `docs/contributing.md` says to run `pytest`, but **there are no test files in the repo** and **no CI workflow runs tests**. `pytest` currently collects nothing.

## Signal processing pipeline (the core domain logic)

In `BrainInterface`, expect these fixed assumptions (module constants at the top of `brain_interface.py`): `SAMPLE_RATE = 250` Hz, single channel (`EEG_CHANNELS = 1`), 5-second circular buffers (`BUFFER_SIZE = 1250`), 115200 baud serial.

Data flow:
1. `_stream_data()` runs in a daemon thread, reads one integer sample per serial line, sign-corrects 24-bit ADC values (`> 0x800000` → subtract `0x1000000`), and writes into circular `raw_buffer`/`filtered_buffer`.
2. Real-time filtering uses **stateful** `signal.lfilter` (1–45 Hz Butterworth bandpass + 60 Hz notch) carrying filter state between samples. Note offline analysis (`_apply_filters`) uses **zero-phase `filtfilt`** instead — two different filter paths exist.
3. `_detect_neural_event()` computes a z-score over a sliding `window_size` (50 samples ≈ 200 ms) and fires an event when `max|z| > detection_threshold` (default 50.0) subject to a `cooldown_period` (default 0.5 s). `calibrate()` exists but currently just hard-codes the threshold to 5.0 rather than deriving it from baseline.
4. Detected events invoke an optional callback registered via `register_event_callback()` — this is how `server.py` mirrors events into its global `session_data` dict.

The server keeps all live state in two module-level globals: `brain_interface` (the device) and `session_data` (a connection/streaming/event summary). All `@method` handlers mutate these.

## Documentation deployment

Three GitHub Actions workflows (`ci.yml`, `docs.yml`, `deploy-docs.yml`) **all run `mkdocs gh-deploy --force` on push to `main`** — they are redundant and all deploy the same MkDocs site to GitHub Pages (custom domain via `docs/CNAME`). The `docs-static/` directory is a separate, manually-maintained HTML site that is **not** wired into any workflow. None of the workflows build, lint, or test the Python code. Editing under `docs/` or `mkdocs.yml` is what triggers a docs redeploy.

To preview docs locally: `pip install mkdocs-material mkdocstrings mkdocstrings-python && mkdocs serve`.
