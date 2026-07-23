"""The pipeline's limitations must be surfaced honestly at every result surface.

These tests exist because the whole value of the disclosure is that it reaches
the human/LLM reading the numbers — so they assert the text is actually present
in MCP output, the CLI, and the dashboard, not just that the module exists.
"""
import time

import pytest

from bci_mcp.dsp.limitations import (
    ANALYSIS_METHOD,
    LIMITATIONS,
    SHORT_DISCLAIMER,
    pipeline_limitations,
)
from bci_mcp.mcp.service import BrainService


def test_limitations_name_the_transient_and_clinical_gaps():
    joined = " ".join(LIMITATIONS).lower()
    assert "transient" in joined
    assert "erp" in joined
    assert "clinical" in joined or "qeeg" in joined
    assert "welch" in SHORT_DISCLAIMER.lower()


def test_pipeline_limitations_structure():
    info = pipeline_limitations()
    assert set(info) >= {"method", "limitations", "disclaimer", "intended_use"}
    assert info["method"] is ANALYSIS_METHOD
    assert "medical" in info["intended_use"].lower() or \
           "not medical" in info["intended_use"].lower()


def test_get_pipeline_limitations_tool():
    out = BrainService().get_pipeline_limitations()
    assert out["limitations"]
    assert "welch" in str(out["method"]).lower()


def test_metric_definitions_carry_method_and_limitations():
    defs = BrainService().get_metric_definitions()
    assert "method" in defs and "limitations" in defs
    assert defs["limitations"]


def test_brain_state_reading_carries_inline_disclaimer():
    svc = BrainService()
    svc.connect("synthetic://?seed=1")
    try:
        state = {"status": "warming_up"}
        for _ in range(50):
            time.sleep(0.1)
            state = svc.get_brain_state()
            if "metrics" in state:
                break
        assert "metrics" in state
        assert state.get("disclaimer") == SHORT_DISCLAIMER
        assert svc.stream_summary().get("disclaimer") == SHORT_DISCLAIMER
    finally:
        svc.disconnect()


def test_server_registers_limitations_tool():
    import asyncio

    from bci_mcp.mcp import server

    tools = asyncio.new_event_loop().run_until_complete(server.mcp.list_tools())
    assert "get_pipeline_limitations" in {t.name for t in tools}


def test_dashboard_exposes_limitations():
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from bci_mcp.dashboard.server import create_app
    from bci_mcp.pipeline import Pipeline

    pipeline = Pipeline("synthetic://?seed=1")
    pipeline.start()
    client = TestClient(create_app(pipeline))
    try:
        info = client.get("/api/info")
        assert info.status_code == 200
        assert info.json()["limitations"]
        home = client.get("/").text
        assert "transients" in home.lower()
    finally:
        pipeline.stop()
