#!/usr/bin/env bash
# One-line installer: curl -fsSL https://raw.githubusercontent.com/enkhbold470/bci-mcp/main/scripts/install-mcp.sh | bash
set -euo pipefail

SCOPE="${BCI_MCP_MCP_SCOPE:-user}"

if ! command -v claude >/dev/null 2>&1; then
  echo "Claude Code CLI not found."
  echo "Install Claude Code: https://code.claude.com/docs/en/mcp"
  echo ""
  echo "Claude Desktop users: add this in Settings → Developer → Edit Config:"
  echo '  "command": "npx", "args": ["-y", "bci-mcp"]'
  exit 1
fi

add_server() {
  # shellcheck disable=SC2068
  claude mcp add --scope "$SCOPE" --transport stdio bci-mcp -- "$@"
}

if command -v npx >/dev/null 2>&1; then
  add_server npx -y bci-mcp
elif command -v uvx >/dev/null 2>&1; then
  add_server uvx bci-mcp serve
elif command -v bci-mcp >/dev/null 2>&1; then
  add_server bci-mcp serve
else
  if command -v pip >/dev/null 2>&1; then
    pip install bci-mcp
    add_server bci-mcp serve
  elif command -v pip3 >/dev/null 2>&1; then
    pip3 install bci-mcp
    add_server bci-mcp serve
  else
    echo "Need Node (npx), uv (uvx), or Python (pip install bci-mcp)."
    exit 1
  fi
fi

echo ""
echo "bci-mcp added (scope: $SCOPE). In Claude Code, run /mcp to confirm."
echo "Try: Connect to the demo brain and tell me my focus level."
