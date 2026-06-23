# Installation

**Python 3.10+** is required. No hardware is needed for the core install — the synthetic device and recording playback work out of the box.

## Core install (synthetic + MCP + CLI)

```bash
git clone https://github.com/enkhbold470/bci-mcp.git
cd bci-mcp
pip install -e "."
```

This installs: `numpy`, `scipy`, `mcp` (official MCP Python SDK), `typer`, `rich`.

## Install extras

| Extra | What it adds | Command |
|---|---|---|
| `devices` | BrainFlow (OpenBCI, Muse), bleak (BLE), pyserial | `pip install -e ".[devices]"` |
| `lsl` | pylsl — consume and publish Lab Streaming Layer streams | `pip install -e ".[lsl]"` |
| `edf` | pyedflib — record/load EDF files | `pip install -e ".[edf]"` |
| `dashboard` | FastAPI + uvicorn — live web dashboard | `pip install -e ".[dashboard]"` |
| `dev` | pytest, ruff, pytest-cov | `pip install -e ".[dev]"` |
| `all` | Everything above | `pip install -e ".[all]"` |

## Verify

```bash
bci-mcp --help
bci-mcp devices
bci-mcp stream --device synthetic:// --once
```

## Next Steps

See [Quick Start](quick-start.md) for the first demo.