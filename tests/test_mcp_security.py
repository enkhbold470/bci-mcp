"""Security tests for BrainService input validation and the HTTP auth layer."""
import time

import pytest

from bci_mcp.mcp.service import (
    MAX_EVENTS,
    MAX_LABEL_CHARS,
    BrainService,
)


@pytest.fixture
def connected(tmp_path, monkeypatch):
    monkeypatch.setenv("BCI_RECORD_DIR", str(tmp_path))
    svc = BrainService()
    assert svc.connect("synthetic://?seed=1")["connected"] is True
    time.sleep(0.3)
    yield svc
    svc.disconnect()


# --- connect ---

def test_connect_rejects_filesystem_schemes_without_raising():
    svc = BrainService()
    for uri in ("playback:///etc/passwd", "serial:///dev/ttyUSB0", "file:///x"):
        out = svc.connect(uri)
        assert "error" in out
    assert "error" in svc.get_brain_state()  # still not connected


def test_connect_bad_device_params_return_error_dict():
    svc = BrainService()
    out = svc.connect("synthetic://?channels=notanumber")
    assert "error" in out
    assert "error" in svc.get_brain_state()  # no half-connected pipeline left


# --- record ---

@pytest.mark.parametrize("seconds", [0, -5, float("nan"), float("inf"), 1e9, "junk"])
def test_record_rejects_bad_durations(connected, seconds):
    out = connected.record(seconds=seconds, path="s.npz")
    assert "error" in out


def test_record_rejects_unknown_format(connected):
    assert "error" in connected.record(seconds=0.2, path="x.exe")
    assert "error" in connected.record(seconds=0.2, path="x.npz", fmt="exe")


def test_record_rejects_traversal_path(connected):
    out = connected.record(seconds=0.2, path="/etc/cron.d/evil.csv", fmt="csv")
    assert "error" in out


# --- calibrate ---

@pytest.mark.parametrize("seconds", [0, -1, float("nan"), 10**6])
def test_calibrate_rejects_bad_durations(connected, seconds):
    assert "error" in connected.calibrate(seconds=seconds)


def test_calibrate_rejects_oversized_condition(connected):
    assert "error" in connected.calibrate(seconds=1, condition="x" * 10_000)


# --- mark_event ---

def test_mark_event_rejects_oversized_label():
    svc = BrainService()
    assert "error" in svc.mark_event("x" * (MAX_LABEL_CHARS + 1))
    assert svc.mark_event("x" * MAX_LABEL_CHARS)["total_events"] == 1


def test_mark_event_storage_is_bounded():
    svc = BrainService()
    for i in range(MAX_EVENTS + 25):
        out = svc.mark_event(f"e{i}")
    assert out["total_events"] == MAX_EVENTS


# --- neurofeedback ---

def test_neurofeedback_rejects_unknown_metric(connected):
    assert "error" in connected.start_neurofeedback(metric="not_a_metric")


@pytest.mark.parametrize("target", [float("nan"), float("inf"), "junk"])
def test_neurofeedback_rejects_bad_target(connected, target):
    assert "error" in connected.start_neurofeedback(metric="focus", target=target)


def test_disconnect_ends_neurofeedback_session(connected):
    assert connected.start_neurofeedback(metric="focus", target=0.5)["started"]
    connected.disconnect()
    assert "error" in connected.get_neurofeedback_score()
