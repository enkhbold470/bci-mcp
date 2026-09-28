"""Shared helpers for the paper benchmarks: environment capture and result I/O."""
from __future__ import annotations

import json
import platform
import subprocess
from importlib import metadata
from pathlib import Path

RESULTS = Path(__file__).resolve().parent.parent / "results"


def _cpu() -> str:
    try:
        if platform.system() == "Darwin":
            return subprocess.check_output(
                ["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return platform.processor() or "unknown"


def environment() -> dict:
    pkgs = {}
    for name in ("bci-mcp", "numpy", "scipy", "mcp", "pyedflib"):
        try:
            pkgs[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            pkgs[name] = None
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True,
            cwd=Path(__file__).parent).strip()
    except Exception:
        commit = None
    return {
        "cpu": _cpu(),
        "os": f"{platform.system()} {platform.release()}",
        "python": platform.python_version(),
        "packages": pkgs,
        "git_commit": commit,
    }


def save(name: str, payload: dict) -> Path:
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / f"{name}.json"
    payload = {"environment": environment(), **payload}
    path.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {path}")
    return path


def pct(values, q: float) -> float:
    import numpy as np

    return float(np.percentile(np.asarray(values, dtype=float), q))
