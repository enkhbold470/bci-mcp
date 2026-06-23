"""Per-metric baseline that maps raw ratios into a personalized 0..1 range."""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field

import numpy as np


@dataclass
class Calibration:
    baseline: dict[str, dict[str, float]] = field(default_factory=dict)

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
                z = value - 1.0  # default: ratio of 1.0 maps to 0.5
            out[key] = 1.0 / (1.0 + math.exp(-z))
        return out

    def to_json(self) -> str:
        return json.dumps({"baseline": self.baseline})

    @classmethod
    def from_json(cls, text: str) -> Calibration:
        return cls(baseline=json.loads(text)["baseline"])

    @classmethod
    def from_samples(cls, raw_list: list[dict[str, float]]) -> Calibration:
        keys = raw_list[0].keys()
        baseline = {
            k: {
                "mean": float(np.mean([r[k] for r in raw_list])),
                "std": float(np.std([r[k] for r in raw_list])),
            }
            for k in keys
        }
        return cls(baseline=baseline)
