"""The unified brain-state snapshot shared by CLI, dashboard, and MCP."""
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class BrainState:
    timestamp: float
    metrics: dict[str, float]
    band_powers: dict[str, float]
    relative_band_powers: dict[str, float]
    signal_quality: str
    quality_score: float
    artifacts: list[str]
    channels: int
    sample_rate: float
    calibrated: bool

    def to_dict(self) -> dict:
        return asdict(self)

    def summary(self) -> str:
        top = ", ".join(f"{k}={v:.2f}" for k, v in self.metrics.items())
        arts = ", ".join(self.artifacts) if self.artifacts else "none"
        cal = "calibrated" if self.calibrated else "uncalibrated"
        return (
            f"[{cal}] {top} | signal: {self.signal_quality} "
            f"({self.quality_score:.2f}) | artifacts: {arts}"
        )
