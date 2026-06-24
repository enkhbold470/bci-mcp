#!/usr/bin/env node
/**
 * Stdio MCP launcher — runs the Python bci-mcp server from PyPI.
 * Tries uvx, then pipx, then a global bci-mcp install.
 */
const { spawnSync } = require("node:child_process");

const attempts = [
  ["uvx", ["bci-mcp", "serve"]],
  ["pipx", ["run", "bci-mcp", "serve"]],
  ["bci-mcp", ["serve"]],
];

function run(cmd, args) {
  const result = spawnSync(cmd, args, {
    stdio: "inherit",
    shell: process.platform === "win32",
  });
  if (result.error?.code === "ENOENT") {
    return null;
  }
  process.exit(result.status ?? 1);
}

for (const [cmd, args] of attempts) {
  const status = run(cmd, args);
  if (status === null) {
    continue;
  }
}

console.error(
  [
    "Could not start bci-mcp MCP server.",
    "",
    "Install one of:",
    "  • uv   → https://docs.astral.sh/uv/   (then: uvx bci-mcp serve)",
    "  • pip  → pip install bci-mcp           (then: bci-mcp serve)",
    "",
    "Docs: https://github.com/enkhbold470/bci-mcp",
  ].join("\n"),
);
process.exit(1);
