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
    """Current brain-state snapshot. (The `seconds` window for rolling stats arrives in a
    later phase; this currently returns the live reading.)"""
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


@mcp.tool()
def record(seconds: float = 10.0, path: str = "session.npz", fmt: str | None = None) -> dict:
    """Record the live stream for N seconds to a file (npz/csv/edf)."""
    return _service.record(seconds, path, fmt)


@mcp.tool()
def start_neurofeedback(metric: str = "focus", target: float = 0.7) -> dict:
    """Begin a neurofeedback session rewarding time spent above a metric target."""
    return _service.start_neurofeedback(metric, target)


@mcp.tool()
def get_neurofeedback_score() -> dict:
    """Sample the current neurofeedback score (in-zone now + cumulative %)."""
    return _service.get_neurofeedback_score()


def serve(transport: str = "stdio") -> None:
    mcp.run(transport=transport)
