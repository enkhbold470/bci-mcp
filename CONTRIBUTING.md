# Contributing to BCI-MCP

Thanks for your interest! BCI-MCP is a Python project (3.10+).

## Setup

```bash
python -m pip install -e ".[all,dev]"
```

## Develop

- Source lives in `src/bci_mcp/`, tests in `tests/`.
- All tests are hardware-free (synthetic device, recording playback, in-process LSL, BrainFlow synthetic board), so you can run the full suite with no headset.
- Before opening a PR:

```bash
ruff check src tests
python -m pytest
```

## Adding a device backend

Implement `bci_mcp.core.device.Device`, return `Chunk(data=(channels, n) float32 µV, timestamps=(n,))`, and register a URI scheme via `bci_mcp.core.registry.register(...)`. See `devices/synthetic.py` for the simplest example and `devices/neurofocus.py` for a real-hardware one.

## Design docs

Specs and implementation plans live under `docs/superpowers/`.
