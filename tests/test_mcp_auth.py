"""Tests for the MCP_AUTH_TOKEN bearer-token middleware."""
import pytest

pytest.importorskip("starlette")

from starlette.testclient import TestClient  # noqa: E402

from bci_mcp.mcp.auth import TokenAuthMiddleware  # noqa: E402


async def _ok_app(scope, receive, send):
    await send({"type": "http.response.start", "status": 200,
                "headers": [(b"content-type", b"text/plain")]})
    await send({"type": "http.response.body", "body": b"ok"})


def test_passthrough_when_no_token_configured(monkeypatch):
    monkeypatch.delenv("MCP_AUTH_TOKEN", raising=False)
    client = TestClient(TokenAuthMiddleware(_ok_app))
    assert client.get("/mcp").status_code == 200


def test_requests_rejected_without_token(monkeypatch):
    monkeypatch.setenv("MCP_AUTH_TOKEN", "s3cret")
    client = TestClient(TokenAuthMiddleware(_ok_app))
    assert client.get("/mcp").status_code == 401
    assert client.post("/mcp").status_code == 401
    wrong = {"Authorization": "Bearer wrong"}
    assert client.get("/mcp", headers=wrong).status_code == 401
    not_bearer = {"Authorization": "Basic s3cret"}
    assert client.get("/mcp", headers=not_bearer).status_code == 401


def test_correct_bearer_token_accepted(monkeypatch):
    monkeypatch.setenv("MCP_AUTH_TOKEN", "s3cret")
    client = TestClient(TokenAuthMiddleware(_ok_app))
    ok = {"Authorization": "Bearer s3cret"}
    assert client.get("/mcp", headers=ok).status_code == 200


def test_health_stays_open_for_probes(monkeypatch):
    monkeypatch.setenv("MCP_AUTH_TOKEN", "s3cret")
    client = TestClient(TokenAuthMiddleware(_ok_app))
    assert client.get("/health").status_code == 200


def test_http_app_is_wrapped_with_auth():
    from bci_mcp.mcp import http_app

    assert isinstance(http_app.app, TokenAuthMiddleware)
