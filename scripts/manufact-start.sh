#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
export MCP_ENV="${MCP_ENV:-production}"
export PATH="${PWD}/.venv/bin:${PATH}"
exec bci-mcp serve --transport streamable-http
