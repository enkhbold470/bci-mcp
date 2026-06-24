# Examples

| File | Description |
|---|---|
| `claude_desktop_config.json` | Claude Desktop MCP config (`npx -y bci-mcp` — no prior install). |
| Claude Code | `claude mcp add bci-mcp -- npx -y bci-mcp` |
| Any (auto) | `curl -fsSL https://raw.githubusercontent.com/enkhbold470/bci-mcp/main/scripts/install-mcp.sh \| bash` |
| `mcp_quickstart.py` | Minimal Python example: connect to the synthetic brain via `BrainService`, read brain state in a loop (no MCP client needed). |
| `record_and_analyze.py` | Record a 2-second synthetic EEG session to `demo_session.npz`, load it, apply a bandpass filter, and print absolute band powers (δ θ α β γ in µV²). |

## Running the examples

```bash
# quickstart (reads 20 × 250 ms frames)
python examples/mcp_quickstart.py

# record + analyze (creates demo_session.npz, then removes it)
python examples/record_and_analyze.py
```
