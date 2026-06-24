# bci-mcp

**Ask Claude what your brain is doing.**

Focus. Calm. Attention. Band powers. Over MCP — the same pipe GitHub, Notion, and the rest use to talk to Claude.

No EEG headset? There’s a built-in demo brain. You can wire this up and have a real conversation about “focus level” before you buy hardware.

---

### What this package actually is

This is **not** the EEG stack. It’s the **doorbell**.

`npx bci-mcp` downloads and runs the Python server from [PyPI](https://pypi.org/project/bci-mcp/). You get Node for install; Python does the signal processing. If `uv` or `pip` isn’t on your machine yet, the launcher will tell you.

---

### Claude Code

```bash
claude mcp add bci-mcp -- npx -y bci-mcp
```

Open Claude, run `/mcp`, make sure `bci-mcp` is green. Then:

> Connect to the demo brain. What’s my focus right now?

---

### Claude Desktop

Settings → Developer → Edit Config:

```json
{
  "mcpServers": {
    "bci-mcp": {
      "command": "npx",
      "args": ["-y", "bci-mcp"]
    }
  }
}
```

Quit Claude fully. Open it again. Same question as above.

---

### Cursor

In `~/.cursor/mcp.json`, under `mcpServers`:

```json
"bci-mcp": {
  "command": "npx",
  "args": ["-y", "bci-mcp"]
}
```

---

### Real hardware

Muse, OpenBCI, NeuroFocus, LSL streams — same server, different device URI. Start with `synthetic://` until the headset is on your desk.

**Repo + docs:** [github.com/enkhbold470/bci-mcp](https://github.com/enkhbold470/bci-mcp)

MIT
