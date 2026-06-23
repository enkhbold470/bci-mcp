import time

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from bci_mcp.dashboard.server import create_app  # noqa: E402
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
