# MCP Integration

BCI-MCP is a genuine **Model Context Protocol** server built with the official [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) (`mcp` on PyPI, `FastMCP`). It runs over **stdio**, which is the standard transport for Claude Desktop integration.

## Claude Desktop setup

1. Install BCI-MCP: `pip install -e ".[all]"`
2. Add to `claude_desktop_config.json`:

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

3. Restart Claude Desktop. BCI-MCP will appear in Claude's tool list.

## MCP Tools

All tools are implemented in `bci_mcp.mcp.server` and backed by `bci_mcp.mcp.service.BrainService`.

| Tool | Signature | Description |
|---|---|---|
| `list_devices` | `() → dict` | List registered URI schemes and auto-discovered devices |
| `connect` | `(device_uri: str = "synthetic://") → dict` | Connect to a device and start streaming |
| `disconnect` | `() → dict` | Stop streaming and release the device |
| `get_brain_state` | `() → dict` | Full `BrainState` snapshot (metrics + band powers + quality) |
| `get_band_powers` | `() → dict` | Absolute and relative band powers (delta, theta, alpha, beta, gamma) |
| `get_signal_quality` | `() → dict` | Quality score, label (good/fair/poor), and artifact list |
| `calibrate` | `(seconds: int = 20, condition: str = "relax") → dict` | Record baseline for personalized metric scaling |
| `record` | `(seconds: float = 10.0, path: str = "session.npz", fmt: str = None) → dict` | Record live stream to file |
| `start_neurofeedback` | `(metric: str = "focus", target: float = 0.7) → dict` | Begin a neurofeedback session |
| `get_neurofeedback_score` | `() → dict` | Current value, in-zone flag, cumulative in-zone % |
| `mark_event` | `(label: str) → dict` | Annotate the stream with a labeled event |
| `stream_summary` | `(seconds: int = 30) → dict` | Live metrics snapshot |

## MCP Resources

| Resource URI | Description |
|---|---|
| `brain://state` | Live `BrainState` as text |
| `brain://device` | Connected device info |

## MCP Prompt

`interpret_brain_state` — tells Claude to call `get_brain_state`, interpret focus/calm/attention in plain language, and suggest one actionable tip.

## Example Claude conversation

> *"Connect to synthetic:// and check my focus level."*

Claude calls:
1. `connect(device_uri="synthetic://")` → `{"connected": true, "device": "Synthetic EEG"}`
2. (waits ~1 s for warmup)
3. `get_brain_state()` → `{"metrics": {"focus": 0.71, "calm": 0.32, ...}, "signal_quality": "good", ...}`

Then responds in natural language.

## Python usage (without Claude)

```python
from bci_mcp.mcp.service import BrainService

svc = BrainService()
svc.connect("synthetic://?focus=0.8&seed=1")

import time; time.sleep(1)  # warmup
state = svc.get_brain_state()
print(state["metrics"])      # {"focus": 0.73, "calm": 0.28, ...}
svc.disconnect()
```