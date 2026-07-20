"""FastAPI dashboard exposing live brain state over REST + WebSocket."""
from __future__ import annotations

import asyncio
from collections.abc import Iterable
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse

from ..pipeline import Pipeline

_STATIC = Path(__file__).parent / "static"

# "testserver" is Starlette's TestClient default; single-label names are not
# resolvable on the public internet, so allowing it does not weaken the check.
_LOCAL_HOSTNAMES = frozenset({"127.0.0.1", "::1", "localhost", "testserver"})


def _hostname(host_header: str) -> str:
    """Hostname from a Host header value ('example.com:8000', '[::1]:8000')."""
    try:
        return urlsplit(f"//{host_header}").hostname or ""
    except ValueError:
        return ""


def _origin_hostname(origin_header: str) -> str:
    try:
        return urlsplit(origin_header).hostname or ""
    except ValueError:
        return ""


def create_app(pipeline: Pipeline, *, extra_allowed_hosts: Iterable[str] = (),
               trust_any_host: bool = False) -> FastAPI:
    """Build the dashboard app.

    The dashboard has no authentication, so it defends the browser boundary
    instead: Host-header validation stops DNS-rebinding pages from becoming
    same-origin with it, and WebSocket Origin validation stops any web page
    from opening ``/ws`` cross-site (browsers do not apply the same-origin
    policy to WebSockets). ``trust_any_host`` disables the Host check for
    all-interface binds, where the legitimate hostnames are unknowable.
    """
    allowed_hosts = _LOCAL_HOSTNAMES | {_hostname(h) or h for h in extra_allowed_hosts}
    app = FastAPI(title="BCI-MCP Dashboard")

    def _host_ok(host_header: str) -> bool:
        return trust_any_host or _hostname(host_header) in allowed_hosts

    def _origin_ok(origin: str | None, host_header: str) -> bool:
        if origin is None:  # non-browser client (curl, python, …)
            return True
        origin_host = _origin_hostname(origin)
        if not origin_host:  # includes the opaque "null" origin
            return False
        # A page legitimately served by this dashboard has Origin == Host.
        return origin_host in allowed_hosts or origin_host == _hostname(host_header)

    @app.middleware("http")
    async def _validate_host(request: Request, call_next):  # noqa: ANN001, ANN202
        if not _host_ok(request.headers.get("host", "")):
            return JSONResponse({"error": "invalid host header"}, status_code=400)
        return await call_next(request)

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(_STATIC / "index.html")

    @app.get("/api/state")
    def state() -> dict:
        s = pipeline.current_state()
        return s.to_dict() if s is not None else {"status": "warming_up"}

    @app.websocket("/ws")
    async def ws(websocket: WebSocket) -> None:
        host_header = websocket.headers.get("host", "")
        origin = websocket.headers.get("origin")
        if not _host_ok(host_header) or not _origin_ok(origin, host_header):
            await websocket.close(code=1008)  # policy violation
            return
        await websocket.accept()
        try:
            while True:
                s = pipeline.current_state()
                await websocket.send_json(s.to_dict() if s is not None
                                          else {"status": "warming_up"})
                await asyncio.sleep(0.25)
        except WebSocketDisconnect:
            pass

    return app


def serve_dashboard(device: str = "synthetic://", host: str = "127.0.0.1",
                    port: int = 8000) -> None:
    import uvicorn

    pipeline = Pipeline(device)
    pipeline.start()
    if host in ("0.0.0.0", "::", ""):
        app = create_app(pipeline, trust_any_host=True)
    else:
        app = create_app(pipeline, extra_allowed_hosts=(host,))
    try:
        uvicorn.run(app, host=host, port=port)
    finally:
        pipeline.stop()
