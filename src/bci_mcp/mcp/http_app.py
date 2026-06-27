"""ASGI entrypoint for Manufact Cloud / streamable HTTP at /mcp."""
from __future__ import annotations

from .server import mcp

app = mcp.streamable_http_app()
