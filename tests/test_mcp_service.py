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
