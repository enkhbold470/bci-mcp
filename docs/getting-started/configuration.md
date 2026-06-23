# Configuration

BCI-MCP is configured primarily through **device URIs** passed to the CLI or MCP tools. There is no config file — every option is a flag or query parameter.

## Device URIs

All device backends are selected via a URI string:

| Backend | URI format | Notes |
|---|---|---|
| Synthetic | `synthetic://` | No hardware; `?focus=0.7&seed=1&channels=4` |
| NeuroFocus (serial) | `neurofocus://serial//dev/tty.usbmodemXXXX` | USB serial |
| NeuroFocus (BLE) | `neurofocus://ble/NEUROFOCUS_V4_01` | BLE name |
| BrainFlow (OpenBCI Cyton) | `brainflow://cyton?serial_port=/dev/ttyUSB0` | |
| BrainFlow (Muse S) | `brainflow://muse_s` | BLE, no extra params |
| LSL | `lsl://YourStreamName` | Any LSL-compatible device |
| Generic serial | `serial:///dev/ttyACM0` | 1 integer per line at baud 115200 |
| Playback | `playback://session.npz` | `?loop=true` to loop |

### Synthetic device query params

| Param | Default | Description |
|---|---|---|
| `focus` | `0.5` | 0..1 — controls alpha/beta mix (0 = high alpha, 1 = high beta) |
| `channels` | `4` | Number of EEG channels |
| `sample_rate` | `256.0` | Hz |
| `seed` | random | RNG seed for reproducible output |

Example:

```bash
bci-mcp stream --device "synthetic://?focus=0.8&channels=8&seed=42"
```

## DSP configuration

The DSP pipeline (`Pipeline`) accepts:

| Parameter | Default | CLI flag | Description |
|---|---|---|---|
| `window_seconds` | `1.0` | — | Welch window length in seconds |
| `notch_freq` | `60.0` Hz | — | Notch filter frequency (50 Hz for Europe) |

These are not yet exposed as CLI flags — edit `Pipeline(device, notch_freq=50.0)` in Python if you need to override.

## Calibration

Run a baseline calibration so metrics are normalized to your personal baseline:

```bash
# Via CLI (after connecting manually in Python, or via MCP tool)
```

Via MCP tool:

```json
{ "tool": "calibrate", "params": { "seconds": 20, "condition": "relax" } }
```

Or in Python:

```python
from bci_mcp.pipeline import Pipeline
pipe = Pipeline("synthetic://")
pipe.start()
pipe.calibrate(seconds=20)  # sit still and relax during this window
```

## Claude Desktop config

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

`bci-mcp serve` uses stdio transport (the standard for Claude Desktop integration).