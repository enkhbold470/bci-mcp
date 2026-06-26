"""Per-metric baseline that maps raw ratios into a personalized 0..1 range."""
from __future__ import annotations

import json
import math
import warnings
from dataclasses import dataclass, field

import numpy as np

# z is clamped before the logistic to avoid math.exp overflow on extreme ratios
# (e.g. a band power collapsing to ~0 in a denominator).
_Z_CLAMP = 60.0


@dataclass
class Calibration:
    baseline: dict[str, dict[str, float]] = field(default_factory=dict)
    # Optional per-metric (center, scale) used only on the uncalibrated path.
    # Empty → every metric defaults to (1.0, 1.0) i.e. ratio of 1.0 maps to 0.5.
    # The pipeline injects metrics.DEFAULT_SCALING so bounded metrics (calm,
    # meditation) are centered at 0.5 instead of being capped low.
    scaling: dict[str, tuple[float, float]] = field(default_factory=dict)

    @property
    def calibrated(self) -> bool:
        return bool(self.baseline)

    def apply(self, raw: dict[str, float]) -> dict[str, float]:
        out: dict[str, float] = {}
        for key, value in raw.items():
            if key in self.baseline:
                mean = self.baseline[key]["mean"]
                std = self.baseline[key]["std"] or 1.0
                z = (value - mean) / std
            else:
                center, scale = self.scaling.get(key, (1.0, 1.0))
                z = (value - center) / (scale or 1.0)
            z = max(-_Z_CLAMP, min(_Z_CLAMP, z))
            out[key] = 1.0 / (1.0 + math.exp(-z))
        return out

    def to_json(self) -> str:
        return json.dumps({"baseline": self.baseline})

    @classmethod
    def from_json(cls, text: str) -> Calibration:
        return cls(baseline=json.loads(text)["baseline"])

    @classmethod
    def from_samples(
        cls,
        raw_list: list[dict[str, float]],
        scaling: dict[str, tuple[float, float]] | None = None,
    ) -> Calibration:
        if not raw_list:
            raise ValueError("from_samples requires at least one sample")
        keys = raw_list[0].keys()
        baseline = {
            k: {
                "mean": float(np.mean([r[k] for r in raw_list])),
                "std": float(np.std([r[k] for r in raw_list])),
            }
            for k in keys
        }
        for k, stats in baseline.items():
            if stats["std"] == 0.0:
                warnings.warn(
                    f"Calibration std=0 for '{k}'; baseline may be degenerate",
                    stacklevel=2,
                )
        return cls(baseline=baseline, scaling=scaling or {})
