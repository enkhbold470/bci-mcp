"""End-to-end MCP latency over the stdio transport.

Spawns ``bci-mcp serve`` as a subprocess exactly as Claude Desktop/Code would,
talks to it with the official MCP Python client, and times:

* cold start: process spawn → ``initialize`` handshake complete;
* ``tools/list``;
* ``connect(synthetic://)`` and time until the first non-warming-up reading;
* steady-state ``get_brain_state`` tool calls (JSON-RPC request → parsed reply).
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import sys
import time
from pathlib import Path

from _common import pct, save
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

CALLS = 500
COLD_STARTS = 10


def _server() -> StdioServerParameters:
    exe = shutil.which("bci-mcp") or str(Path(sys.executable).with_name("bci-mcp"))
    env = {k: v for k, v in os.environ.items() if k not in ("PORT", "MCP_ENV")}
    return StdioServerParameters(command=exe, args=["serve"], env=env)


def _payload(result) -> dict:
    return json.loads(result.content[0].text)


async def cold_start() -> float:
    t0 = time.perf_counter()
    async with stdio_client(_server()) as (r, w), ClientSession(r, w) as s:
        await s.initialize()
        return (time.perf_counter() - t0) * 1e3


async def steady_state() -> dict:
    async with stdio_client(_server()) as (r, w), ClientSession(r, w) as s:
        await s.initialize()
        t0 = time.perf_counter()
        tools = await s.list_tools()
        list_ms = (time.perf_counter() - t0) * 1e3

        t0 = time.perf_counter()
        out = _payload(await s.call_tool("connect", {"device_uri": "synthetic://?seed=1"}))
        connect_ms = (time.perf_counter() - t0) * 1e3
        assert out.get("connected"), out

        t0 = time.perf_counter()
        while True:
            state = _payload(await s.call_tool("get_brain_state", {}))
            if "metrics" in state:
                break
        first_reading_ms = (time.perf_counter() - t0) * 1e3

        times, sizes = [], []
        for _ in range(CALLS):
            t0 = time.perf_counter()
            res = await s.call_tool("get_brain_state", {})
            state = _payload(res)
            times.append((time.perf_counter() - t0) * 1e3)
            sizes.append(len(res.content[0].text.encode()))
            assert "metrics" in state
        await s.call_tool("disconnect", {})
        return {
            "tool_count": len(tools.tools),
            "tools_list_ms": list_ms,
            "connect_ms": connect_ms,
            "time_to_first_reading_ms": first_reading_ms,
            "get_brain_state": {
                "calls": CALLS, "median_ms": pct(times, 50), "p95_ms": pct(times, 95),
                "p99_ms": pct(times, 99), "median_payload_bytes": pct(sizes, 50),
            },
        }


async def main() -> None:
    colds = [await cold_start() for _ in range(COLD_STARTS)]
    steady = await steady_state()
    result = {
        "transport": "stdio",
        "device": "synthetic://?seed=1 (4 ch @ 256 Hz, 32-sample chunks)",
        "cold_start_ms": {"runs": COLD_STARTS, "median": pct(colds, 50),
                          "p95": pct(colds, 95)},
        **steady,
    }
    print(json.dumps(result, indent=2))
    save("mcp_roundtrip", result)


if __name__ == "__main__":
    asyncio.run(main())
