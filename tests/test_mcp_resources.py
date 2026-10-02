"""MCP resources must be valid JSON that a client can parse.

These read through the registered server, the same path a client takes, and
json.loads the result: Python repr (single quotes, None, True) would fail here.
"""
import asyncio
import json
import time

import pytest

from bci_mcp.mcp import server

JSON_RESOURCES = ("brain://state", "brain://device", "brain://citations")


def _read(uri: str):
    loop = asyncio.new_event_loop()
    try:
        return json.loads(list(loop.run_until_complete(server.mcp.read_resource(uri)))[0].content)
    finally:
        loop.close()


@pytest.fixture
def connected():
    server._service.connect("synthetic://?seed=1")
    try:
        yield server._service
    finally:
        server._service.disconnect()


def test_resources_advertise_json():
    loop = asyncio.new_event_loop()
    try:
        resources = loop.run_until_complete(server.mcp.list_resources())
    finally:
        loop.close()
    mime = {str(r.uri): r.mimeType for r in resources}
    for uri in JSON_RESOURCES:
        assert mime[uri] == "application/json", uri


def test_state_resource_when_not_connected_is_json():
    server._service.disconnect()
    assert "error" in _read("brain://state")


def test_state_resource_matches_live_reading(connected):
    state = {}
    for _ in range(50):
        time.sleep(0.1)
        state = _read("brain://state")
        if "metrics" in state:
            break
    assert "metrics" in state
    assert set(state["metrics"]) == set(state["metric_confidence"])
    assert state["status"] in {"ok", "unreliable"}
    assert isinstance(state["calibrated"], bool)
    assert state["disclaimer"]


def test_device_resource_is_json():
    devices = _read("brain://device")
    assert {"uri": "synthetic://", "name": "Synthetic EEG (no hardware)",
            "needs_hardware": False} in devices["devices"]
    assert "synthetic" in devices["schemes"]
