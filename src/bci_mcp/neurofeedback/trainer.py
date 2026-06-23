"""Neurofeedback training session: reward time spent above a metric target."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NeurofeedbackSummary:
    metric: str
    target: float
    samples: int
    time_in_zone_pct: float
    mean_score: float
    best_streak: int


class NeurofeedbackSession:
    def __init__(self, pipeline, metric: str = "focus", target: float = 0.7) -> None:
        self.pipeline = pipeline
        self.metric = metric
        self.target = target
        self._values: list[float] = []
        self._in_zone = 0
        self._streak = 0
        self._best_streak = 0
        self._last_in_zone = False

    def start(self) -> None:
        self._values.clear()
        self._in_zone = 0
        self._streak = 0
        self._best_streak = 0
        self._last_in_zone = False

    def sample(self) -> float | None:
        state = self.pipeline.current_state()
        if state is None or self.metric not in state.metrics:
            return None
        value = float(state.metrics[self.metric])
        self._values.append(value)
        if value >= self.target:
            self._in_zone += 1
            self._streak += 1
            self._best_streak = max(self._best_streak, self._streak)
            self._last_in_zone = True
        else:
            self._streak = 0
            self._last_in_zone = False
        return value

    def score(self) -> dict:
        n = len(self._values)
        return {
            "metric": self.metric,
            "target": self.target,
            "current": self._values[-1] if self._values else None,
            "in_zone": self._last_in_zone,
            "cumulative_in_zone_pct": (100.0 * self._in_zone / n) if n else 0.0,
            "samples": n,
        }

    def summary(self) -> NeurofeedbackSummary:
        n = len(self._values)
        return NeurofeedbackSummary(
            metric=self.metric, target=self.target, samples=n,
            time_in_zone_pct=(100.0 * self._in_zone / n) if n else 0.0,
            mean_score=(sum(self._values) / n) if n else 0.0,
            best_streak=self._best_streak,
        )
