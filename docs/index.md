# 🧠 BCI-MCP — Plug your brain into any AI

> A real [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server that streams live EEG brain state — focus, calm, attention — from *any* EEG device (or a built-in synthetic brain) straight into Claude and any MCP client.

**BCI-MCP** is a brain–computer interface (BCI) toolkit and a genuine **Model Context Protocol server**. It reads an EEG signal from hardware or a built-in synthetic brain, turns it into real-time cognitive metrics, and exposes them to AI assistants like **Claude Desktop** via MCP tools and resources.

## Any EEG device

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

## Quickstart

```bash
git clone https://github.com/enkhbold470/bci-mcp.git
cd bci-mcp
pip install -e ".[all]"

bci-mcp devices                       # list connectable devices/URIs
bci-mcp stream --device synthetic://  # live terminal brain-meter (no hardware)
bci-mcp dashboard                     # live web dashboard at http://127.0.0.1:8000
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

## Architecture

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

## Links

- [Installation](getting-started/installation.md)
- [Quick Start](getting-started/quick-start.md)
- [Configuration](getting-started/configuration.md)
- [MCP Integration](features/mcp-integration.md)
- [API Reference](api/bci-module.md)
- [GitHub](https://github.com/enkhbold470/bci-mcp)
