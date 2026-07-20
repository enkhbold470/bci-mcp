"""ASGI entrypoint for Manufact Cloud / streamable HTTP at /mcp."""
from __future__ import annotations

from .auth import TokenAuthMiddleware
from .server import mcp

# Bearer auth engages only when MCP_AUTH_TOKEN is set (see auth.py).
app = TokenAuthMiddleware(mcp.streamable_http_app())
