"""The unified brain-state snapshot shared by CLI, dashboard, and MCP."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field


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
    # How much to trust this reading (0..1): folds in signal quality, whether a
    # baseline has been calibrated, and how full the analysis window was.
    confidence: float = 1.0
    # Per-metric confidence (same keys as ``metrics``); lets consumers discount
    # individual values rather than the whole snapshot.
    metric_confidence: dict[str, float] = field(default_factory=dict)
    # "ok" | "warming_up" | "unreliable". "unreliable" means a hard artifact or
    # poor signal contaminated this window — the metrics are still present but
    # should not be interpreted as a clean reading.
    status: str = "ok"

    def to_dict(self) -> dict:
        return asdict(self)

    def summary(self) -> str:
        top = ", ".join(f"{k}={v:.2f}" for k, v in self.metrics.items())
        arts = ", ".join(self.artifacts) if self.artifacts else "none"
        cal = "calibrated" if self.calibrated else "uncalibrated"
        flag = "" if self.status == "ok" else f" [{self.status}]"
        return (
            f"[{cal}]{flag} {top} | signal: {self.signal_quality} "
            f"({self.quality_score:.2f}, conf {self.confidence:.2f}) | "
            f"artifacts: {arts}"
        )
