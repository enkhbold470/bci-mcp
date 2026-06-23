# BCI-MCP

A [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server that streams live EEG brain state — focus, calm, attention — from an EEG device (or a built-in synthetic signal) into Claude and other MCP clients.

[![CI](https://github.com/enkhbold470/bci-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/enkhbold470/bci-mcp/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-7c3aed)](https://modelcontextprotocol.io)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://enkhbold470.github.io/bci-mcp/)

BCI-MCP is a small brain–computer interface (BCI) toolkit built around one idea: read an EEG signal, turn it into a few honest real-time metrics, and make those available to an AI assistant through MCP. The signal can come from an [OpenBCI](https://openbci.com) board, a [Muse](https://choosemuse.com) headband, a NeuroFocus device, any [Lab Streaming Layer](https://labstreaminglayer.org) stream, or a synthetic generator that needs no hardware — so you can try the whole thing before you own a headset.

```
$ bci-mcp stream --device synthetic://

  FOCUS        ##############......  0.71
  CALM         ######..............  0.32
  ATTENTION    #################...  0.86
  ENGAGEMENT   ##############......  0.70
  alpha ####  beta #######  theta ##  delta #  gamma ###     signal: GOOD
```

## What you get

- One interface for several EEG sources. The same code path drives a synthetic device, NeuroFocus over USB or BLE, OpenBCI and Muse (via BrainFlow), any LSL stream, and a generic one-integer-per-line serial device.
- A real MCP server, built on the official MCP Python SDK (FastMCP), running over stdio so it drops straight into Claude Desktop.
- A signal-processing pipeline: band powers (delta, theta, alpha, beta, gamma) from a Welch PSD, a handful of derived metrics (focus, calm, attention, engagement, fatigue, meditation), basic signal-quality and artifact checks, and an optional per-person calibration step.
- The usual surrounding tools: a terminal brain-meter, a web dashboard, a neurofeedback session, session recording (CSV/npz/EDF) with replay, and an LSL publisher.
- Tests that run without hardware — a synthetic device, recording playback, an in-process LSL loop, and BrainFlow's synthetic board — so `pip install` and `pytest` work anywhere. CI covers Python 3.10–3.12.

## Any EEG device

| Device | URI | Install |
|---|---|---|
| Synthetic (no hardware) | `synthetic://` | core |
| NeuroFocus v4 (USB serial) | `neurofocus://serial//dev/tty.usbmodemXXXX` | `[devices]` |
| NeuroFocus v4 (BLE) | `neurofocus://ble/NEUROFOCUS_V4_01` | `[devices]` |
| OpenBCI Cyton/Ganglion | `brainflow://cyton?serial_port=/dev/ttyUSB0` | `[devices]` |
| Muse 2 / S | `brainflow://muse_s` | `[devices]` |
| Any LSL stream | `lsl://YourStreamName` | `[lsl]` |
| Generic serial (1 int/line) | `serial:///dev/ttyACM0` | `[devices]` |
| Recording replay | `playback://session.npz` | core |

## Quickstart

```bash
git clone https://github.com/enkhbold470/bci-mcp.git
cd bci-mcp
python -m pip install -e ".[all]"     # or just "." for the core synthetic + MCP path

bci-mcp devices                       # list connectable devices/URIs
bci-mcp stream --device synthetic://  # live terminal brain-meter (no hardware)
bci-mcp dashboard                     # live web dashboard at http://127.0.0.1:8000
```

Record a session and play it back later:

```bash
bci-mcp record --device synthetic:// --seconds 30 --out session.npz
bci-mcp play session.npz
```

Run a neurofeedback session:

```bash
bci-mcp neurofeedback --device synthetic:// --metric focus --target 0.7
```

## Using it from Claude Desktop

Add this to your Claude Desktop MCP config (`claude_desktop_config.json`):

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

Then you can ask things like "What's my current focus level?" or "Run a 60-second neurofeedback session and tell me how I did," and Claude will call the tools below.

- Tools: `list_devices`, `connect`, `disconnect`, `get_brain_state`, `get_band_powers`, `get_signal_quality`, `calibrate`, `record`, `start_neurofeedback`, `get_neurofeedback_score`, `mark_event`, `stream_summary`.
- Resources: `brain://state`, `brain://device`. Prompt: `interpret_brain_state`.

## How it fits together

```
EEG device -> Device (synthetic | neurofocus | brainflow | lsl | serial | playback)
                 |  Chunk (channels x samples, microvolts)
                 v
              Stream --> RingBuffer --> consumers
                 v
            DSP Pipeline  (bandpass/notch -> Welch band powers -> metrics -> quality)
                 |  BrainState (focus, calm, attention, ..., signal quality)
                 +--> CLI brain-meter / web dashboard
                 +--> neurofeedback trainer
                 +--> recorder (CSV / npz / EDF)  <-->  PlaybackDevice
                 +--> LSL publisher
                 +--> MCP server (FastMCP, stdio)  -->  Claude / any MCP client
```

## Install options

```bash
pip install -e "."              # core: numpy, scipy, mcp, typer, rich (synthetic + MCP + CLI)
pip install -e ".[devices]"     # + brainflow, bleak, pyserial (OpenBCI, Muse, NeuroFocus, serial)
pip install -e ".[lsl]"         # + pylsl (consume/publish Lab Streaming Layer)
pip install -e ".[edf]"         # + pyedflib (EDF recording)
pip install -e ".[dashboard]"   # + fastapi, uvicorn (web dashboard)
pip install -e ".[all]"         # everything
```

## A note on accuracy

The metrics here are simple, well-understood band-power ratios, not clinical measures. They are useful for neurofeedback, demos, and experimentation, and they are documented in the source so you can see exactly how each one is computed.

## Documentation

Full docs: https://enkhbold470.github.io/bci-mcp/

## Disclaimer

BCI-MCP is for research, education, and personal experimentation. It is not a medical device and must not be used for diagnosis or treatment.

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). Please run `ruff check src tests && pytest` before opening a PR.

## License

MIT — see [LICENSE](LICENSE).

---

Topics: EEG, BCI, brain-computer interface, Model Context Protocol, MCP, Claude, neurofeedback, OpenBCI, Muse, BrainFlow, Lab Streaming Layer (LSL), brainwave, neurotech, neuroscience, Python, real-time signal processing, band power, alpha/beta/theta, focus tracking.
