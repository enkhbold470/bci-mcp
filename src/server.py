"""Manufact Cloud entrypoint — `uvicorn src.server:app --host 0.0.0.0 --port 8000`."""
from __future__ import annotations

from bci_mcp.mcp.http_app import app

__all__ = ["app"]
