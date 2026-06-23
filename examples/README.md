# Examples

| File | Description |
|---|---|
| `claude_desktop_config.json` | Drop this into your Claude Desktop MCP config to wire `bci-mcp serve` as an MCP server. |
| `mcp_quickstart.py` | Minimal Python example: connect to the synthetic brain via `BrainService`, read brain state in a loop (no MCP client needed). |
| `record_and_analyze.py` | Record a 2-second synthetic EEG session to `demo_session.npz`, load it, apply a bandpass filter, and print absolute band powers (δ θ α β γ in µV²). |

## Running the examples

```bash
# quickstart (reads 20 × 250 ms frames)
python examples/mcp_quickstart.py

# record + analyze (creates demo_session.npz, then removes it)
python examples/record_and_analyze.py
```
