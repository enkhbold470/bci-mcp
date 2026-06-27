"""BCI-MCP — plug your brain into any AI."""

from . import devices as _devices  # noqa: F401  (triggers device registration)
from .mcp.http_app import app

__version__ = "0.2.0"
__all__ = ["__version__", "app"]
