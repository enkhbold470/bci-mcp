import time

import numpy as np
import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from bci_mcp.dashboard.server import create_app  # noqa: E402
from bci_mcp.devices.synthetic import SyntheticDevice  # noqa: E402
from bci_mcp.pipeline import Pipeline  # noqa: E402


def test_dashboard_serves_html_and_state():
    pipeline = Pipeline("synthetic://?seed=1")
    pipeline.start()
    time.sleep(0.5)
    app = create_app(pipeline)
    client = TestClient(app)
    try:
        home = client.get("/")
        assert home.status_code == 200
        assert "BCI-MCP" in home.text

        state = client.get("/api/state")
        assert state.status_code == 200
        body = state.json()
        # warming_up dict or a full BrainState dict
        assert "metrics" in body or "status" in body
    finally:
        pipeline.stop()


def test_synthetic_control_changes_generated_band_mix():
    device = SyntheticDevice(seed=1, chunk_samples=512)
    device.start()
    client = TestClient(create_app(Pipeline(device)))
    assert client.get("/api/synthetic").json() == {"focus": 0.5}

    def band_ratio():
        data = device.read().data[0]
        spectrum = np.abs(np.fft.rfft(data)) ** 2
        return spectrum[40] / spectrum[20]  # 20 Hz / 10 Hz at 256 Hz over 2 s

    headers = {"Origin": "http://testserver"}
    assert client.post("/api/synthetic", json={"focus": 0.0}, headers=headers).status_code == 200
    low = band_ratio()
    assert client.post("/api/synthetic", json={"focus": 1.0}, headers=headers).status_code == 200
    high = band_ratio()
    assert high > low * 10
    assert client.get("/api/synthetic").json() == {"focus": 1.0}


@pytest.mark.parametrize("origin", [None, "http://evil.example.com", "https://testserver",
                                    "http://testserver:1234", "http://[bad"])
def test_synthetic_control_rejects_cross_origin_requests(origin):
    pipeline = Pipeline("synthetic://")
    client = TestClient(create_app(pipeline))
    headers = {"Origin": origin} if origin else {}
    response = client.post("/api/synthetic", json={"focus": 1.0}, headers=headers)
    assert response.status_code == 403
    assert pipeline.device.focus == 0.5


@pytest.mark.parametrize("value", [-0.1, 1.1, "0.5", True])
def test_synthetic_control_rejects_invalid_values(value):
    pipeline = Pipeline("synthetic://")
    client = TestClient(create_app(pipeline))
    response = client.post("/api/synthetic", json={"focus": value},
                           headers={"Origin": "http://testserver"})
    assert response.status_code == 422
    assert pipeline.device.focus == 0.5


def test_synthetic_control_unavailable_for_other_devices():
    pipeline = Pipeline("synthetic://")
    pipeline.device = object()
    client = TestClient(create_app(pipeline))
    assert client.get("/api/synthetic").status_code == 404
    response = client.post("/api/synthetic", json={"focus": 0.5},
                           headers={"Origin": "http://testserver"})
    assert response.status_code == 404


def test_dashboard_rejects_foreign_host_header():
    """DNS-rebinding defense: unknown Host headers are refused."""
    pipeline = Pipeline("synthetic://?seed=1")
    pipeline.start()
    client = TestClient(create_app(pipeline))
    try:
        rebound = client.get("/api/state", headers={"Host": "evil.example.com"})
        assert rebound.status_code == 400
        assert client.get("/api/state").status_code == 200  # testserver still fine
    finally:
        pipeline.stop()


def test_dashboard_allows_extra_host():
    pipeline = Pipeline("synthetic://?seed=1")
    pipeline.start()
    client = TestClient(create_app(pipeline, extra_allowed_hosts=("192.168.1.5",)))
    try:
        lan = client.get("/api/state", headers={"Host": "192.168.1.5:8000"})
        assert lan.status_code == 200
    finally:
        pipeline.stop()


def test_websocket_rejects_cross_site_origin():
    """CSWSH defense: browsers don't apply SOP to WebSockets, the server must."""
    pipeline = Pipeline("synthetic://?seed=1")
    pipeline.start()
    from starlette.websockets import WebSocketDisconnect

    client = TestClient(create_app(pipeline))
    try:
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(
                    "/ws", headers={"Origin": "http://evil.example.com"}) as ws:
                ws.receive_json()
    finally:
        pipeline.stop()


def test_websocket_allows_local_origin_and_no_origin():
    pipeline = Pipeline("synthetic://?seed=1")
    pipeline.start()
    client = TestClient(create_app(pipeline))
    try:
        with client.websocket_connect(
                "/ws", headers={"Origin": "http://testserver"}) as ws:
            body = ws.receive_json()
            assert "metrics" in body or "status" in body
        with client.websocket_connect("/ws") as ws:  # curl/python clients
            body = ws.receive_json()
            assert "metrics" in body or "status" in body
    finally:
        pipeline.stop()
