# 🧠 BCI-MCP — Plug your brain into any AI

> **A real [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server that streams live EEG brain state — focus, calm, attention — from *any* EEG device (or a built-in synthetic brain) straight into Claude and any MCP client.**

[![CI](https://github.com/enkhbold470/bci-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/enkhbold470/bci-mcp/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-7c3aed)](https://modelcontextprotocol.io)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://enkhbold470.github.io/bci-mcp/)

**BCI-MCP** is a brain–computer interface (BCI) toolkit and a genuine **Model Context Protocol server**. It reads an EEG (electroencephalography) signal — from an [OpenBCI](https://openbci.com) board, a [Muse](https://choosemuse.com) headband, a NeuroFocus device, any [Lab Streaming Layer](https://labstreaminglayer.org) source, or a **built-in synthetic brain that needs no hardware** — turns it into real-time cognitive metrics, and exposes them to AI assistants like **Claude Desktop** as MCP tools and resources. Your AI can literally read and reason about your brain state.

```
$ bci-mcp stream --device synthetic

  FOCUS        ██████████████░░░░░░  0.71
  CALM         ██████░░░░░░░░░░░░░░  0.32
  ATTENTION    █████████████████░░░  0.86
  ENGAGEMENT   ██████████████░░░░░░  0.70
  α ████  β ███████  θ ██  δ █  γ ███     signal: GOOD
```

---

## ✨ Why BCI-MCP

- 🔌 **Any EEG device** — one URI, every backend. Synthetic, NeuroFocus (USB + BLE), OpenBCI, Muse, anything on LSL, or a generic serial stream.
- 🤖 **A real MCP server** — not a toy. Built on the official MCP Python SDK (FastMCP), it plugs into **Claude Desktop** and any MCP client over stdio.
- 🧪 **Works with zero hardware** — a synthetic brain + recording playback mean `pip install` → working demo → green CI, no headset required.
- 📊 **Real neuroscience** — band powers (δ θ α β γ via Welch PSD), focus/calm/attention/engagement/fatigue metrics, signal-quality + artifact detection, personalized calibration.
- 🎮 **Batteries included** — live terminal brain-meter, web dashboard, neurofeedback trainer, session recording (CSV/npz/EDF) + replay, and an LSL publisher for the wider BCI ecosystem.
- ✅ **Tested & typed** — 75+ hardware-free tests, ruff-clean, CI on Python 3.10–3.12.

## 🧰 Any EEG device

| Device | URI | Install |
|---|---|---|
| **Synthetic** (no hardware) | `synthetic://` | core |
| **NeuroFocus v4** (USB serial) | `neurofocus://serial//dev/tty.usbmodemXXXX` | `[devices]` |
| **NeuroFocus v4** (BLE) | `neurofocus://ble/NEUROFOCUS_V4_01` | `[devices]` |
| **OpenBCI** Cyton/Ganglion | `brainflow://cyton?serial_port=/dev/ttyUSB0` | `[devices]` |
| **Muse** 2 / S | `brainflow://muse_s` | `[devices]` |
| **Any LSL stream** | `lsl://YourStreamName` | `[lsl]` |
| **Generic serial** (1 int/line) | `serial:///dev/ttyACM0` | `[devices]` |
| **Recording replay** | `playback://session.npz` | core |

## 🚀 Quickstart

```bash
git clone https://github.com/enkhbold470/bci-mcp.git
cd bci-mcp
python -m pip install -e ".[all]"     # or just "." for the core synthetic + MCP path

bci-mcp devices                       # list connectable devices/URIs
bci-mcp stream --device synthetic://  # live terminal brain-meter (no hardware)
bci-mcp dashboard                     # live web dashboard at http://127.0.0.1:8000
```

Record and replay a session (great for demos and offline analysis):

```bash
bci-mcp record --device synthetic:// --seconds 30 --out session.npz
bci-mcp play session.npz
```

Train your focus:

```bash
bci-mcp neurofeedback --device synthetic:// --metric focus --target 0.7
```

## 🤖 Use it from Claude Desktop

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

Then ask Claude things like *"What's my current focus level?"* or *"Run a 60-second neurofeedback session and tell me how I did."* Claude calls the MCP tools below.

**MCP tools:** `list_devices`, `connect`, `disconnect`, `get_brain_state`, `get_band_powers`, `get_signal_quality`, `calibrate`, `record`, `start_neurofeedback`, `get_neurofeedback_score`, `mark_event`, `stream_summary`.
**MCP resources:** `brain://state`, `brain://device`. **Prompt:** `interpret_brain_state`.

## 🏗️ Architecture

```
EEG device ─► Device (synthetic │ neurofocus │ brainflow │ lsl │ serial │ playback)
                 │  Chunk (channels × samples, µV)
                 ▼
              Stream ──► RingBuffer ──► consumers
                 ▼
            DSP Pipeline  (bandpass/notch → Welch band powers → metrics → quality)
                 │  BrainState (focus, calm, attention, …, signal quality)
                 ├──► CLI brain-meter / web dashboard
                 ├──► neurofeedback trainer
                 ├──► recorder (CSV / npz / EDF)  ◄──► PlaybackDevice
                 ├──► LSL publisher
                 └──► MCP server (FastMCP, stdio)  ──►  Claude / any MCP client
```

## 📦 Install options

```bash
pip install -e "."              # core: numpy, scipy, mcp, typer, rich (synthetic + MCP + CLI)
pip install -e ".[devices]"     # + brainflow, bleak, pyserial (OpenBCI, Muse, NeuroFocus, serial)
pip install -e ".[lsl]"         # + pylsl (consume/publish Lab Streaming Layer)
pip install -e ".[edf]"         # + pyedflib (EDF recording)
pip install -e ".[dashboard]"   # + fastapi, uvicorn (web dashboard)
pip install -e ".[all]"         # everything
```

## 🧠 Keywords

EEG · BCI · brain-computer interface · Model Context Protocol · MCP · Claude · AI · neurofeedback · OpenBCI · Muse · BrainFlow · Lab Streaming Layer (LSL) · brainwave · neurotech · neuroscience · Python · real-time signal processing · band power · alpha/beta/theta · focus tracking.

## 📚 Documentation

Full docs: **https://enkhbold470.github.io/bci-mcp/**

## ⚠️ Disclaimer

BCI-MCP is for research, education, and personal experimentation. It is **not a medical device** and must not be used for diagnosis or treatment.

## 🤝 Contributing

Contributions welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). Run `ruff check src tests && pytest` before opening a PR.

## 📄 License

MIT — see [LICENSE](LICENSE).

Project Link: [https://github.com/enkhbold470/bci-mcp](https://github.com/enkhbold470/bci-mcp)