"""Heuristic signal-quality assessment and artifact flags."""
from __future__ import annotations

import numpy as np


def assess_quality(data: np.ndarray, fs: float) -> tuple[float, str, list[str]]:
    artifacts: list[str] = []
    var = float(np.mean(np.var(data, axis=-1)))
    if var < 1e-3:
        return 0.0, "no_contact", ["flatline"]

    amp = float(np.mean(np.ptp(data, axis=-1)))  # mean peak-to-peak across channels
    score = 1.0
    if amp > 2000.0:  # rail-to-rail swing
        artifacts.append("railing")
        score -= 0.6
    elif amp > 400.0:  # implausibly large for scalp EEG
        score -= 0.25
    if float(np.max(np.abs(data[0]))) > 150.0 and amp <= 2000.0:
        artifacts.append("blink")

    score = max(0.0, min(1.0, score))
    label = "good" if score > 0.75 else "fair" if score > 0.4 else "poor"
    return score, label, artifacts
