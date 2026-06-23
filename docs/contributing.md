# Contributing to BCI-MCP

Thanks for your interest! See the root [CONTRIBUTING.md](https://github.com/enkhbold470/bci-mcp/blob/main/CONTRIBUTING.md) for full instructions.

## Quick setup

```bash
git clone https://github.com/enkhbold470/bci-mcp.git
cd bci-mcp
python -m pip install -e ".[all,dev]"
```

## Before opening a PR

```bash
ruff check src tests
python -m pytest
```

All tests are hardware-free — no EEG headset needed.

## Adding a device backend

Implement `bci_mcp.core.device.Device`, return `Chunk(data=(channels, n) float32 µV, timestamps=(n,))`, and register a URI scheme via `bci_mcp.core.registry.register(...)`. See `devices/synthetic.py` for the simplest example. 