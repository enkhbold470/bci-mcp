"""FastAPI dashboard exposing live brain state over REST + WebSocket."""
from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from ..pipeline import Pipeline

_STATIC = Path(__file__).parent / "static"


def create_app(pipeline: Pipeline) -> FastAPI:
    app = FastAPI(title="BCI-MCP Dashboard")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(_STATIC / "index.html")

    @app.get("/api/state")
    def state() -> dict:
        s = pipeline.current_state()
        return s.to_dict() if s is not None else {"status": "warming_up"}

    @app.websocket("/ws")
    async def ws(websocket: WebSocket) -> None:
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
    app = create_app(pipeline)
    try:
        uvicorn.run(app, host=host, port=port)
    finally:
        pipeline.stop()
