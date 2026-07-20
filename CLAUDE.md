# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Git commits

**Never add `Co-authored-by` trailers** (Cursor, Claude, or any AI). See [AGENTS.md](AGENTS.md). This is enforced mechanically: the repo sets `core.hooksPath = .githooks` and `.githooks/prepare-commit-msg` strips any AI `Co-authored-by:` line. A fresh clone must run `git config core.hooksPath .githooks` to get that protection. Verify with `git log -1 --format='%B'` before pushing. (Unrelated: the root `hooks.py` is a **MkDocs** build hook — writes `sitemap.xml`, copies `llms.txt`/`.nojekyll` — not a git hook.)

## What this project is

**BCI-MCP** (version `0.2.0`) is a Python package (`src/bci_mcp/`) that provides:

- **Device-agnostic EEG acquisition** via a URI registry (synthetic, NeuroFocus serial+BLE, BrainFlow/OpenBCI/Muse, LSL, generic serial, recording playback).
- **A real MCP server** built on the official MCP Python SDK (`mcp` on PyPI, `FastMCP`), exposing live brain state to Claude Desktop and any MCP client. Runs over **stdio** (local) or **streamable-HTTP** (cloud) — see [Deployment & transports](#deployment--transports).
- **A DSP pipeline** that turns raw EEG into `BrainState` (focus, calm, attention, engagement, fatigue, meditation + δθαβγ band powers + signal quality + confidence).
- **A Rich CLI** with commands: `devices`, `stream`, `record`, `play`, `neurofeedback`, `dashboard`, `serve` (+ `mcp`, an alias of `serve`).
- **Recording** (CSV/npz/EDF) + replay, neurofeedback trainer, LSL publisher, FastAPI web dashboard.

## Package layout

```
src/bci_mcp/
├── __init__.py            # device registration + re-exports ASGI `app`; __version__ = "0.2.0"
├── cli.py                 # Typer CLI (entry point: bci-mcp)
├── pipeline.py            # Pipeline: Device → Stream → DSP → BrainState
├── core/
│   ├── device.py          # Device ABC, Chunk, DeviceInfo dataclasses
│   ├── registry.py        # URI registry (register/create_device/discover)
│   ├── ringbuffer.py      # RingBuffer (multi-channel circular numpy buffer)
│   └── stream.py          # Stream (single daemon thread polling device.read())
├── devices/
│   ├── synthetic.py       # SyntheticDevice — no hardware needed
│   ├── neurofocus.py      # NeuroFocus v4 (serial + BLE); uses neurofocus_protocol
│   ├── neurofocus_protocol.py # pure (I/O-free) NeuroFocus wire-protocol decode
│   ├── brainflow_device.py # BrainFlow (OpenBCI, Muse, ...)
│   ├── lsl_device.py      # LSL consumer
│   ├── serial_device.py   # Generic serial (1 int/line)
│   └── playback.py        # PlaybackDevice (npz/csv/edf replay)
├── dsp/
│   ├── filters.py         # notch + bandpass (zero-phase, scipy.signal.filtfilt)
│   ├── bands.py           # band_powers() via Welch PSD, relative_band_powers()
│   ├── metrics.py         # raw_metrics() + METRIC_INFO (formula/literature/caveat per metric)
│   ├── state.py           # BrainState dataclass (incl. confidence + status)
│   ├── quality.py         # assess_quality() — signal score + HARD_ARTIFACTS flags
│   └── calibration.py     # Calibration — personalized z-score / default sigmoid scaling
├── mcp/
│   ├── server.py          # FastMCP tools/resources/prompt + serve()
│   ├── service.py         # BrainService — testable core (server.py wraps this)
│   ├── auth.py            # TokenAuthMiddleware — optional MCP_AUTH_TOKEN bearer auth
│   └── http_app.py        # ASGI entrypoint (serves /mcp), wrapped in TokenAuthMiddleware
├── recording/
│   ├── recorder.py        # Recorder stream consumer
│   ├── writer.py          # save_recording() — npz/csv/edf
│   ├── reader.py          # load_recording() → Recording dataclass
│   └── paths.py           # MCP security: sandbox record paths + allow-list device URIs
├── neurofeedback/trainer.py   # NeurofeedbackSession
├── lsl/publisher.py           # LSL outlet publisher
└── dashboard/
    ├── server.py          # FastAPI web dashboard
    └── static/index.html  # dashboard UI (served at /)
```

`recording/paths.py` is **security-critical**: `safe_record_path()` sandboxes all MCP recording I/O to `$BCI_RECORD_DIR` (default `~/bci-recordings`) and rejects path traversal (incl. symlink escapes and directory targets); `validate_mcp_uri()` + `MCP_ALLOWED_SCHEMES = {synthetic, brainflow, lsl, neurofocus}` reject `playback://`/`serial://` over MCP (they grant filesystem/device access). Both are enforced in `mcp/service.py` (`connect`, `record`), which additionally treats every MCP tool argument as untrusted: durations are validated and capped (`MAX_RECORD_SECONDS`/`MAX_CALIBRATE_SECONDS`), recording formats and neurofeedback metrics are allowlisted, event labels/list are size-capped, and `connect`/`record` return `{"error": ...}` dicts instead of raising. See `SECURITY.md` for the full threat model.

**Repo-root deploy glue (not in the wheel):** `src/server.py` + `src/__init__.py` re-export the ASGI app for `uvicorn src.server:app` in a checkout. The wheel ships only `src/bci_mcp` (`[tool.hatch.build.targets.wheel]`), so edits to `src/server.py` do **not** affect the installed package.

## Install and run

```bash
pip install -e ".[all,dev]"          # editable + all extras + dev tools (CONTRIBUTING default)

bci-mcp devices                      # list URI schemes + discovered hardware
bci-mcp stream --device synthetic:// # live terminal brain-meter
bci-mcp stream --device synthetic:// --once   # single snapshot (CI smoke path)
bci-mcp record --device synthetic:// --seconds 10 --out session.npz   # --fmt npz|csv|edf
bci-mcp play session.npz             # internally streams playback://<abs-path>?loop=true
bci-mcp neurofeedback --device synthetic:// --metric focus --target 0.7 --seconds 30
bci-mcp dashboard --device synthetic://   # warns when --host is non-loopback (no auth)
bci-mcp serve                        # MCP server (stdio by default)
```

### Dependencies & extras

Build backend is **hatchling**. Core deps are minimal (`numpy`, `scipy`, `mcp`, `typer`, `rich`); hardware/feature backends are optional extras, so a bare `pip install bci-mcp` ImportErrors on any real device until the matching extra is added:

| Extra | Pulls in | Enables |
|-------|----------|---------|
| `devices` | brainflow, bleak, pyserial | OpenBCI/Muse, NeuroFocus BLE, generic serial |
| `dashboard` | fastapi, uvicorn, websockets | `bci-mcp dashboard` + the `bci_mcp:app` HTTP server |
| `lsl` | pylsl | LSL consumer device + publisher |
| `edf` | pyedflib | EDF recording read/write |
| `dev` | pytest, pytest-cov, ruff, build | tests + lint + build |
| `docs` | mkdocs-shadcn, mkdocstrings, … | `mkdocs build` |

`all` = `devices,dashboard,lsl,edf` only (it does **not** include `dev`/`docs`). **`uv` is canonical for build/publish/locked installs** (`uv build`, `uv publish`, `uv sync --frozen`; `uv.lock` is committed); **`pip install -e` is what CI tests and contributors use.** Reach for pip in local dev, uv for releases.

## Tests & CI

```bash
ruff check src tests                  # linter (line-length 100, rules E,F,I,UP,B; must be clean)
python -m pytest                      # all tests (testpaths=["tests"])
python -m pytest tests/test_bands.py # single file
python -m pytest -k test_focus       # by name pattern
mkdocs build --strict                 # docs MUST build with zero warnings (a CI gate)
```

All tests are **hardware-free**: synthetic device, recording playback, in-process LSL, BrainFlow synthetic board. No EEG headset needed.

`.github/workflows/ci.yml` gates every push/PR across Python **3.10/3.11/3.12** (supported range) on, in order: `ruff check` → `pytest` → `mkdocs build --strict`, plus a separate `npm pack --dry-run` job. So a docs/mkdocs change that warns, or a broken npm launcher, fails CI even when pytest passes.

**Releases are tag-driven and need a triple version bump.** `publish.yml` fires on `v*` tags and hard-fails unless the tag matches **all of** `pyproject.toml` `version`, `npm/bci-mcp/package.json` `version`, and `server.json` (`version` **and** every `packages[].version`). Bump all three to the same `X.Y.Z`, then tag. (All currently aligned at `0.2.0`.) Publishing is OIDC trusted publishing (PyPI via `uv publish`, npm via `npm publish --provenance`). `server.json` (MCP registry manifest) publishes separately via the `mcp-publisher` CLI — see CONTRIBUTING. Ownership markers that must track `server.json`'s `name`: `mcpName` in `npm/bci-mcp/package.json` and the `<!-- mcp-name: … -->` comment atop `README.md`.

## Architecture

```
Device.read() → Chunk → Stream (daemon thread) → RingBuffer (holds sample_rate × 10 s)
                                                          │
Pipeline.current_state() pulls latest `window` samples (~2 s), runs:
  filters.notch  (60 Hz, Q=30 — applied FIRST, before it can fold into passband)
  → filters.bandpass  (1–45 Hz, order-4 Butterworth, zero-phase filtfilt)
  → bands.band_powers  (Welch PSD, nperseg ≈ 1 s, 50% overlap)
  → metrics.raw_metrics
  → calibration.apply → BrainState
                                                          │
Consumers: CLI brain-meter, FastMCP server, FastAPI dashboard,
           Recorder (→ npz/csv/edf), LSL publisher, NeurofeedbackSession
```

**Non-obvious internals** (read these before touching the pipeline):

- **Stream threading.** `Stream.start()` spawns one `threading.Thread(daemon=True)` looping `device.read()` → `RingBuffer.write()`. A single `Lock` guards only the buffer write/`latest()`. Consumer callbacks (e.g. `Recorder`) added via `add_consumer` run **synchronously on the producer thread**, outside the lock; exceptions are caught and logged (a throwing consumer won't crash acquisition, but a slow one stalls it). The 10 s ring buffer is independent of the 2 s analysis window.
- **Warming-up & status.** `current_state()` returns `None` until the buffer has `max(int(0.5·fs), 64)` samples; `BrainService` maps that to `{"status": "warming_up"}`. So `warming_up` is a **service-layer sentinel** — `BrainState.status` itself is only ever `"ok"` or `"unreliable"` (forced unreliable by a hard artifact like flatline/railing or `signal_quality=="poor"`).
- **Confidence.** `confidence = clamp(quality_score × cal_factor × fill, 0, 1)` with `cal_factor = 1.0` calibrated / `0.6` not, `fill = min(1, samples/window)`; capped at `0.1` when unreliable. `metric_confidence` is currently this single scalar copied to every metric key (uniform, not per-metric).
- **Metrics use only θ/α/β.** delta & gamma are excluded from every metric (EMG/drift-dominated) but still reported as raw band powers. `focus=β/(α+θ)`, `engagement=β/α` (a distinct ratio, *not* a duplicate of focus), `calm=α/(α+β)`, `attention=β/θ`, `fatigue=(θ+α)/β`, `meditation=α/(α+β+θ)`. Full formula + literature + caveat per metric live in `metrics.METRIC_INFO`, surfaced by the `get_metric_definitions` MCP tool.
- **Calibration is two-path.** Uncalibrated: logistic over `metrics.DEFAULT_SCALING` (bounded metrics centered 0.5, unbounded ratios centered 1.0). Calibrated: per-metric z-score (clamped ±60) from a baseline built by `Pipeline.calibrate(seconds=20)`.

## Device URI registry

Every device backend calls `bci_mcp.core.registry.register(scheme, factory)` at import time (triggered by `bci_mcp/__init__.py`). `create_device(uri)` parses the URI + query string and dispatches; an empty/bare scheme defaults to `synthetic`. Schemes: `synthetic`, `neurofocus`, `brainflow`, `lsl`, `serial`, `playback`.

## MCP server

`bci_mcp.mcp.server` uses `FastMCP` from the official MCP Python SDK. `server.py` is a thin adapter: each `@mcp.tool()` is a one-line delegate to a module-level singleton `_service = BrainService()` (`service.py`), so the server holds **exactly one** live Pipeline/connection at a time (`connect()` stops any prior one). `BrainService` never raises for control flow — it returns sentinel dicts (`{"error": ...}` when not connected, `{"status": "warming_up"}` before the first reading); derived tools detect this via `if "metrics" not in state`. **Tests target `BrainService` directly** (no transport needed) — put testable logic there, wiring in `server.py`.

- **Tools (13):** `list_devices`, `connect`, `disconnect`, `get_brain_state`, `get_band_powers`, `get_signal_quality`, `get_metric_definitions`, `calibrate`, `mark_event`, `stream_summary`, `record`, `start_neurofeedback`, `get_neurofeedback_score`.
- **Resources:** `brain://state`, `brain://device`. **Prompt:** `interpret_brain_state`.

## Deployment & transports

`bci-mcp serve --transport {stdio|sse|streamable-http}` (default `stdio`; `bci-mcp mcp` is an alias). stdio is for local Claude Desktop/Code; **streamable-http** serves MCP at `/mcp` plus a non-MCP `GET /health` → `{"status":"healthy"}`. The ASGI `app` object is built once in `mcp/http_app.py` (the streamable-HTTP app wrapped in `TokenAuthMiddleware`) and re-exported as **`bci_mcp:app`** (canonical, works from the installed wheel — point uvicorn here) and `src.server:app` (checkout only). `serve()` applies the same auth wrapper to its sse/streamable-http paths, and loopback binds get SDK DNS-rebinding protection (Host/Origin validation).

**Env vars reconfigure the running server** (read in `mcp/server.py`):

| Var | Effect |
|---|---|
| `PORT` | Listen port. Its mere presence **also** forces host `0.0.0.0` **and auto-upgrades `serve` from stdio → streamable-http** — this is how a stdio-default image becomes an HTTP server on a host. |
| `MCP_ENV=production` | Forces `0.0.0.0` + `stateless_http=True`. |
| `FASTMCP_HOST` / `FASTMCP_PORT` | Explicit host/port. |
| `FASTMCP_STATELESS_HTTP` | Stateless HTTP sessions. |
| `BCI_RECORD_DIR` | Output dir for the `record` tool (Docker sets `/data`). |
| `MCP_AUTH_TOKEN` | When set, HTTP transports require `Authorization: Bearer <token>` on every request except `GET /health` (`mcp/auth.py`). Unset = open; `serve()` warns when binding non-loopback without it. |

**Deploy targets each build differently:**

- **Docker / compose** (`Dockerfile`, `docker-compose.yml`): `python:3.12-slim`, `pip install .`, non-root `appuser`, `ENTRYPOINT ["bci-mcp"]`, `CMD ["serve"]` → **stdio** (no port). `BCI_RECORD_DIR=/data` (VOLUME). To serve HTTP, set `PORT` or override the command.
- **Railway** (`railway.toml`): `builder = "DOCKERFILE"` — reuses the Dockerfile and injects `PORT`, so the stdio `CMD` auto-upgrades to HTTP.
- **Manufact Cloud** (`manufact.toml`, `scripts/manufact-start.sh`): does **not** use Docker — uv buildpack runs `uv sync --frozen --no-dev` then `uvicorn bci_mcp:app --host 0.0.0.0 --port 8000` (requires `uv.lock` committed; leave dashboard build/start commands empty so they auto-detect). Clients connect to `https://<slug>.run.mcp-use.com/mcp`.
- **npm wrapper** (`npm/bci-mcp/`, separate package, own version): a thin stdio launcher — `bin.js` tries `uvx` → `pipx run` → global `bci-mcp serve`. `npx -y bci-mcp` is the recommended Claude Desktop/Code command (wired in root `.mcp.json`); `scripts/install-mcp.sh` runs `claude mcp add … --transport stdio`.

## Design docs

Specs and implementation plans live under `docs/superpowers/`.
