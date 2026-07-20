"""Safe path resolution for recording I/O."""
from __future__ import annotations

import os
from pathlib import Path


def _allowed_dir() -> Path:
    env = os.environ.get("BCI_RECORD_DIR")
    return Path(env).resolve() if env else (Path.home() / "bci-recordings").resolve()


def safe_record_path(path: str) -> str:
    """Resolve *path* to an absolute path inside BCI_RECORD_DIR.

    Raises ValueError on traversal attempts.  When *path* is already absolute
    and inside the allowed directory it is returned as-is; otherwise the
    basename is appended to the allowed directory.
    """
    allowed = _allowed_dir()
    p = Path(path)
    if p.is_absolute():
        resolved = p.resolve()
    else:
        # Strip any directory components from relative paths — use name only.
        resolved = (allowed / p.name).resolve()
    if not str(resolved).startswith(str(allowed) + os.sep):
        raise ValueError(
            f"Recording path '{path}' is outside the allowed directory '{allowed}'. "
            f"Set BCI_RECORD_DIR to change the allowed directory."
        )
    if resolved.is_dir():
        raise ValueError(f"Recording path '{path}' is a directory, not a file.")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return str(resolved)


# Allowlist of URI schemes permitted via MCP tool calls.
# playback:// and serial:// grant filesystem/device access and must not be
# accepted from untrusted MCP clients.
MCP_ALLOWED_SCHEMES = frozenset({"synthetic", "brainflow", "lsl", "neurofocus"})


def validate_mcp_uri(device_uri: str) -> str:
    """Raise ValueError if *device_uri* uses a scheme not allowed over MCP."""
    from urllib.parse import urlparse

    scheme = urlparse(device_uri).scheme.lower()
    if scheme not in MCP_ALLOWED_SCHEMES:
        raise ValueError(
            f"Device URI scheme '{scheme}' is not permitted via MCP. "
            f"Allowed schemes: {', '.join(sorted(MCP_ALLOWED_SCHEMES))}."
        )
    return device_uri
