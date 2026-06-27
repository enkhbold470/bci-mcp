"""Real Model Context Protocol server exposing live brain state."""
from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

from .service import BrainService


def _listen_host() -> str:
    if os.environ.get("PORT") or os.environ.get("MCP_ENV") == "production":
        return os.environ.get("FASTMCP_HOST", "0.0.0.0")
    return os.environ.get("FASTMCP_HOST", "127.0.0.1")


def _listen_port() -> int:
    return int(os.environ.get("FASTMCP_PORT", os.environ.get("PORT", "8000")))


mcp = FastMCP("bci-mcp", host=_listen_host(), port=_listen_port())
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
    """Get the current brain state. Returns heuristic band-power proxy metrics
    (focus, calm, attention, engagement, fatigue, meditation), band powers, and
    signal quality. Each reading carries `confidence` (0..1), per-metric
    `metric_confidence`, and a `status` ('ok'/'warming_up'/'unreliable') — weight
    the metrics by these and do not interpret an unreliable/low-confidence
    reading. Call get_metric_definitions to learn what each metric means."""
    return _service.get_brain_state()


@mcp.tool()
def get_band_powers() -> dict:
    """Get absolute and relative EEG band powers (delta, theta, alpha, beta, gamma)."""
    return _service.get_band_powers()


@mcp.tool()
def get_signal_quality() -> dict:
    """Get electrode signal quality, reading confidence, and detected artifacts
    (blink, railing, emg, flatline)."""
    return _service.get_signal_quality()


@mcp.tool()
def get_metric_definitions() -> dict:
    """Explain each brain metric: its exact formula, the literature it draws on,
    and an honest caveat. Call this to learn what focus/calm/attention/engagement/
    fatigue/meditation actually measure and how much to trust them — they are
    heuristic proxies, not validated cognitive measurements."""
    return _service.get_metric_definitions()


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
        "Call get_brain_state (and get_metric_definitions if unsure what the "
        "numbers mean). These metrics are heuristic EEG band-power proxies, not "
        "validated cognitive measurements: weight them by the `confidence` / "
        "`metric_confidence` fields and the `signal_quality`/`status`. If status "
        "is 'unreliable' or confidence is low, say the reading can't be trusted "
        "rather than interpreting it. Otherwise explain in plain language what "
        "the wearer's focus, calm, and attention levels *suggest* (not prove) "
        "about their state, and offer one actionable tip."
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
