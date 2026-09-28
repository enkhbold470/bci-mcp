"""Per-reading compute cost of the DSP pipeline (no transport).

Fills a Pipeline's ring buffer directly from a SyntheticDevice (no producer
thread, so timing is not polluted by acquisition sleeps), then times
``Pipeline.current_state()`` — notch, bandpass, Welch band power, metrics,
calibration mapping and quality assessment on the latest 2 s window.
"""
from __future__ import annotations

import time

import numpy as np
from _common import pct, save

from bci_mcp.devices.synthetic import SyntheticDevice
from bci_mcp.pipeline import Pipeline

CONFIGS = [  # (channels, sample_rate, label)
    (1, 256.0, "1 ch @ 256 Hz"),
    (4, 256.0, "4 ch @ 256 Hz (Muse-like)"),
    (8, 250.0, "8 ch @ 250 Hz (OpenBCI Cyton-like)"),
    (16, 125.0, "16 ch @ 125 Hz (Cyton+Daisy-like)"),
    (64, 160.0, "64 ch @ 160 Hz (BCI2000 cap)"),
]
REPS = 2000
WARMUP = 50


def run_config(channels: int, fs: float) -> dict:
    dev = SyntheticDevice(channels=channels, sample_rate=fs, seed=0)
    pipe = Pipeline(dev)
    dev.start()
    # Fill the whole 10 s ring buffer.
    while len(pipe.stream.buffer) < pipe.stream.buffer.capacity:
        pipe.stream.buffer.write(dev.read().data)
    for _ in range(WARMUP):
        pipe.current_state()
    times = []
    for _ in range(REPS):
        t0 = time.perf_counter()
        state = pipe.current_state()
        times.append((time.perf_counter() - t0) * 1e3)
    assert state is not None
    return {
        "channels": channels, "sample_rate": fs, "window_samples": pipe.window,
        "reps": REPS, "median_ms": pct(times, 50), "p95_ms": pct(times, 95),
        "p99_ms": pct(times, 99), "mean_ms": float(np.mean(times)),
    }


def main() -> None:
    rows = []
    for ch, fs, label in CONFIGS:
        r = run_config(ch, fs)
        r["label"] = label
        rows.append(r)
        print(f"{label:38s} median {r['median_ms']:.3f} ms  p95 {r['p95_ms']:.3f} ms")
    save("compute", {"window_seconds": 2.0, "results": rows})


if __name__ == "__main__":
    main()
