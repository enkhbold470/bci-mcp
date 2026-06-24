import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_claude_desktop_config_valid():
    cfg = json.loads((ROOT / "examples" / "claude_desktop_config.json").read_text())
    entry = cfg["mcpServers"]["bci-mcp"]
    assert entry["command"] in {"npx", "bci-mcp", "uvx"}
    if entry["command"] == "npx":
        assert "bci-mcp" in entry.get("args", [])


def test_quickstart_is_importable_module(tmp_path):
    # The example must at least parse/compile.
    src = (ROOT / "examples" / "mcp_quickstart.py").read_text()
    compile(src, "mcp_quickstart.py", "exec")
