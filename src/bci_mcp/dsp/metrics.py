"""Cognitive metrics derived from band powers (documented heuristics)."""
from __future__ import annotations

METRIC_NAMES = ("focus", "calm", "attention", "engagement", "fatigue", "meditation")
_EPS = 1e-9


def raw_metrics(bp: dict[str, float]) -> dict[str, float]:
    """Unscaled metric ratios. Calibration maps these into 0..1 later."""
    d, t, a, b, g = (bp["delta"], bp["theta"], bp["alpha"], bp["beta"], bp["gamma"])
    total = d + t + a + b + g + _EPS
    return {
        "focus": b / (a + t + _EPS),          # concentration (beta vs alpha+theta)
        "calm": a / (a + b + _EPS),           # relaxation (alpha vs beta)
        "attention": b / (t + _EPS),          # beta vs theta
        "engagement": (b + g) / (a + t + d + _EPS),  # Pope-style engagement
        "fatigue": (t + d) / (a + b + _EPS),  # drowsiness
        "meditation": t / total,              # relative theta
    }
