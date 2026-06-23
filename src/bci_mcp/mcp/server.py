"""Real Model Context Protocol server exposing live brain state."""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .service import BrainService

mcp = FastMCP("bci-mcp")
_service = BrainService()


@mcp.tool()
def list_devices() -> dict:
    """List EEG devices/URIs you can connect to."""
    return _service.list_devices()


@mcp.tool()
def connect(device_uri: str = "synthetic://") -> dict:
    """Connect to an EEG device and start streaming. Default is the synthetic brain."""
    return _service.connect(device_uri)


@mcp.tool()
def disconnect() -> dict:
    """Disconnect from the current EEG device."""
    return _service.disconnect()


@mcp.tool()
def get_brain_state() -> dict:
    """Get the current brain state: focus, calm, attention, band powers, signal quality."""
    return _service.get_brain_state()


@mcp.tool()
def get_band_powers() -> dict:
    """Get absolute and relative EEG band powers (delta, theta, alpha, beta, gamma)."""
    return _service.get_band_powers()


@mcp.tool()
def get_signal_quality() -> dict:
    """Get electrode signal quality and detected artifacts (blink, railing, …)."""
    return _service.get_signal_quality()


@mcp.tool()
def calibrate(seconds: int = 20, condition: str = "relax") -> dict:
    """Capture a baseline so focus/calm/etc. are personalized to the wearer."""
    return _service.calibrate(seconds, condition)


@mcp.tool()
def mark_event(label: str) -> dict:
    """Annotate the live stream with a labeled event marker."""
    return _service.mark_event(label)


@mcp.tool()
def stream_summary(seconds: int = 30) -> dict:
    """Summarize recent brain activity over the last N seconds."""
    return _service.stream_summary(seconds)


@mcp.resource("brain://state")
def brain_state_resource() -> str:
    """Live brain-state snapshot as text."""
    state = _service.get_brain_state()
    return str(state)


@mcp.resource("brain://device")
def brain_device_resource() -> str:
    """Information about the connected device."""
    return str(_service.list_devices())


@mcp.prompt()
def interpret_brain_state() -> str:
    """Prompt template: ask the model to interpret the current brain state."""
    return (
        "Call get_brain_state, then explain in plain language what the wearer's "
        "focus, calm, and attention levels suggest about their current cognitive "
        "state, and suggest one actionable tip."
    )


def serve(transport: str = "stdio") -> None:
    mcp.run(transport=transport)
