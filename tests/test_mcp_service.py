import time

from bci_mcp.mcp.service import BrainService


def test_connect_then_get_state():
    svc = BrainService()
    assert svc.get_brain_state()["error"]  # not connected yet

    out = svc.connect("synthetic://?seed=1")
    assert out["connected"] is True
    try:
        state = {"status": "warming_up"}
        for _ in range(50):
            time.sleep(0.1)
            state = svc.get_brain_state()
            if "metrics" in state:
                break
        assert "metrics" in state
        assert "focus" in state["metrics"]

        bands = svc.get_band_powers()
        assert "alpha" in bands["band_powers"]

        quality = svc.get_signal_quality()
        assert "signal_quality" in quality
    finally:
        svc.disconnect()


def test_list_devices_includes_synthetic():
    svc = BrainService()
    out = svc.list_devices()
    assert any("synthetic" in d["uri"] for d in out["devices"])


def test_server_module_registers_tools():
    from bci_mcp.mcp import server

    assert server.mcp is not None
    assert callable(server.serve)


def test_methods_report_not_connected():
    svc = BrainService()
    assert "error" in svc.get_band_powers()
    assert "error" in svc.get_signal_quality()
    assert "error" in svc.stream_summary()


def test_mark_event_increments():
    svc = BrainService()
    assert svc.mark_event("baseline")["total_events"] == 1
    assert svc.mark_event("task")["total_events"] == 2


def test_record_and_neurofeedback(tmp_path, monkeypatch):
    import time

    monkeypatch.setenv("BCI_RECORD_DIR", str(tmp_path))
    svc = BrainService()
    svc.connect("synthetic://?seed=1")
    try:
        time.sleep(0.5)
        out = svc.record(seconds=0.4, path=str(tmp_path / "s.npz"))
        assert out["path"].endswith(".npz")

        started = svc.start_neurofeedback(metric="focus", target=0.5)
        assert started["metric"] == "focus"
        time.sleep(0.4)
        for _ in range(5):
            time.sleep(0.1)
            score = svc.get_neurofeedback_score()
        assert "cumulative_in_zone_pct" in score
    finally:
        svc.disconnect()


def test_neurofeedback_requires_connection():
    svc = BrainService()
    assert "error" in svc.start_neurofeedback()
    assert "error" in svc.get_neurofeedback_score()
