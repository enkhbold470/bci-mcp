# Security Policy

## Reporting a vulnerability

Please report suspected vulnerabilities privately via
[GitHub security advisories](https://github.com/enkhbold470/bci-mcp/security/advisories/new)
rather than public issues. You should get a response within a week.

## Threat model

BCI-MCP handles live EEG — biometric data — and exposes it to MCP clients and
a web dashboard, so the codebase treats every MCP tool argument and every HTTP
request as untrusted:

- **Recording sandbox.** The MCP `record` tool can only write inside
  `BCI_RECORD_DIR` (default `~/bci-recordings`). Path traversal, symlink
  escapes, and prefix-sibling tricks are rejected
  (`bci_mcp/recording/paths.py`).
- **Device-URI allowlist.** MCP clients may only connect `synthetic://`,
  `brainflow://`, `lsl://`, and `neurofocus://` devices. `playback://` and
  `serial://` are refused over MCP because they grant filesystem/device-path
  access.
- **Bounded tool inputs.** Durations for `record`/`calibrate` are validated
  (finite, positive, capped) so a client cannot stall the single shared
  pipeline indefinitely; event labels and the event list are size-capped;
  recording formats and neurofeedback metrics are allowlisted.
- **HTTP authentication.** Set `MCP_AUTH_TOKEN` when serving MCP over
  streamable-HTTP/SSE and every request (except `GET /health`) must send
  `Authorization: Bearer <token>`. Unset, the HTTP server is open — fine on
  loopback, and the server logs a warning if it binds a public interface
  without a token.
- **Browser-boundary defenses.** Loopback HTTP MCP serving validates
  Host/Origin headers (DNS-rebinding protection). The dashboard validates the
  Host header and requires WebSocket Origins to be local (or the served host),
  blocking cross-site WebSocket hijacking of live brain data.

## Deployment guidance

- Prefer the **stdio** transport for local Claude Desktop/Code use; nothing
  listens on the network.
- For cloud deployments (Railway, Manufact, Docker with `PORT`), always set
  `MCP_AUTH_TOKEN` to a long random secret and serve behind TLS.
- Keep the dashboard on `127.0.0.1` unless you understand that binding a LAN
  host exposes unauthenticated brain-state data to that network.
- Recordings contain raw EEG. Point `BCI_RECORD_DIR` at storage with
  appropriate access controls before recording real sessions.
