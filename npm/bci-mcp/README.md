# bci-mcp

**Stream live EEG brain state — focus, calm, attention — into Claude.** Demo mode works with no headset.

This npm package is a thin **npx** launcher for the Python server on [PyPI](https://pypi.org/project/bci-mcp/). It runs `uvx bci-mcp serve` (or pipx / a global `bci-mcp` install).

**Requires:** Node (for npx) plus [uv](https://docs.astral.sh/uv/) or Python (`pip install bci-mcp`).

## Claude Code (one line)

```bash
claude mcp add bci-mcp -- npx -y bci-mcp
```

## Claude Desktop

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

## Cursor

Add under `mcpServers` in `~/.cursor/mcp.json`:

```json
"bci-mcp": {
  "command": "npx",
  "args": ["-y", "bci-mcp"]
}
```

Then ask: *“Connect to the demo brain — what’s my focus?”*

Docs: [github.com/enkhbold470/bci-mcp](https://github.com/enkhbold470/bci-mcp)
