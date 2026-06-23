# Quick Start

No EEG hardware needed — the **synthetic device** generates realistic brainwaves so you can run the full demo with just `pip install`.

## 1. Install

```bash
git clone https://github.com/enkhbold470/bci-mcp.git
cd bci-mcp
pip install -e ".[all]"
```

## 2. Check available devices

```bash
bci-mcp devices
```

Lists every URI scheme registered (synthetic, neurofocus, brainflow, lsl, serial, playback) and any auto-discovered hardware.

## 3. Live terminal brain-meter

```bash
bci-mcp stream --device synthetic://
```

Press Ctrl-C to stop. Add `--once` to print a single snapshot:

```bash
bci-mcp stream --device synthetic:// --once
```

## 4. Record a session

```bash
bci-mcp record --device synthetic:// --seconds 30 --out session.npz
```

Formats: `.npz` (default), `.csv`, `.edf` (needs `[edf]` extra). Replay with:

```bash
bci-mcp play session.npz
```

## 5. Neurofeedback trainer

```bash
bci-mcp neurofeedback --device synthetic:// --metric focus --target 0.7 --seconds 60
```

Prints a live indicator showing whether your metric is in-zone, then a session summary.

## 6. Web dashboard

```bash
bci-mcp dashboard
```

Opens at `http://127.0.0.1:8000` — shows live band powers and metrics.

## 7. MCP server for Claude Desktop

```bash
bci-mcp serve
```

Or point Claude Desktop at it in `claude_desktop_config.json`:

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

Then ask Claude: *"Connect to the synthetic brain and tell me my current focus level."*

## Available CLI commands

| Command | Description |
|---|---|
| `bci-mcp devices` | List registered URI schemes and discovered devices |
| `bci-mcp stream` | Live terminal brain-meter (Ctrl-C to quit) |
| `bci-mcp record` | Record a session to file |
| `bci-mcp play` | Replay a recording |
| `bci-mcp neurofeedback` | Run a neurofeedback session |
| `bci-mcp dashboard` | Launch FastAPI web dashboard |
| `bci-mcp serve` | Start the MCP server (stdio, for Claude Desktop) |