"""Testable brain-service core. server.py adapts this to MCP."""
from __future__ import annotations

import time

from ..pipeline import Pipeline
from ..recording.paths import safe_record_path, validate_mcp_uri


class BrainService:
    def __init__(self) -> None:
        self._pipeline: Pipeline | None = None
        self._events: list[dict] = []
        self._nf = None

    def list_devices(self) -> dict:
        from ..core.registry import discover, list_schemes

        return {"devices": discover(), "schemes": list_schemes()}

    def connect(self, device_uri: str = "synthetic://") -> dict:
        validate_mcp_uri(device_uri)
        if self._pipeline is not None:
            self._pipeline.stop()
        self._pipeline = Pipeline(device_uri)
        self._pipeline.start()
        return {"connected": True, "device": self._pipeline.device.info.name,
                "uri": device_uri}

    def disconnect(self) -> dict:
        if self._pipeline is not None:
            self._pipeline.stop()
            self._pipeline = None
        return {"connected": False}

    def get_brain_state(self) -> dict:
        if self._pipeline is None:
            return {"error": "not connected — call connect() first"}
        state = self._pipeline.current_state()
        return state.to_dict() if state is not None else {"status": "warming_up"}

    def get_band_powers(self) -> dict:
        state = self.get_brain_state()
        if "metrics" not in state:  # error / warming_up sentinel
            return state
        return {"band_powers": state["band_powers"],
                "relative_band_powers": state["relative_band_powers"],
                "confidence": state["confidence"]}

    def get_signal_quality(self) -> dict:
        state = self.get_brain_state()
        if "metrics" not in state:  # error / warming_up sentinel
            return state
        return {"signal_quality": state["signal_quality"],
                "quality_score": state["quality_score"],
                "artifacts": state["artifacts"],
                "confidence": state["confidence"],
                "status": state["status"]}

    def get_metric_definitions(self) -> dict:
        from ..dsp.metrics import METRIC_INFO

        return {
            "metrics": METRIC_INFO,
            "disclaimer": (
                "These are heuristic EEG band-power ratios, not validated "
                "clinical measurements. Weight them by the `confidence` and "
                "`metric_confidence` fields, treat `status` == 'unreliable' as "
                "untrustworthy, and calibrate for personalized 0-1 scaling."
            ),
        }

    def calibrate(self, seconds: int = 20, condition: str = "relax") -> dict:
        if self._pipeline is None:
            return {"error": "not connected"}
        cal = self._pipeline.calibrate(seconds=seconds)
        return {"calibrated": cal.calibrated, "condition": condition,
                "metrics": list(cal.baseline)}

    def mark_event(self, label: str) -> dict:
        self._events.append({"label": label, "timestamp": time.time()})
        return {"marked": label, "total_events": len(self._events)}

    def stream_summary(self, seconds: int = 30) -> dict:
        # Plan 1: report the instantaneous state; rolling stats arrive with recording.
        state = self.get_brain_state()
        if "metrics" not in state:
            return state
        return {"window_seconds": seconds, "current": state["metrics"],
                "metric_confidence": state["metric_confidence"],
                "confidence": state["confidence"],
                "signal_quality": state["signal_quality"],
                "status": state["status"]}

    def record(self, seconds: float = 10.0, path: str = "session.npz",
               fmt: str | None = None) -> dict:
        if self._pipeline is None:
            return {"error": "not connected"}
        try:
            safe_path = safe_record_path(path)
        except ValueError as exc:
            return {"error": str(exc)}
        out = self._pipeline.record(seconds=seconds, path=safe_path, fmt=fmt)
        return {"recorded": True, "path": out, "seconds": seconds}

    def start_neurofeedback(self, metric: str = "focus", target: float = 0.7) -> dict:
        if self._pipeline is None:
            return {"error": "not connected"}
        from ..neurofeedback.trainer import NeurofeedbackSession

        self._nf = NeurofeedbackSession(self._pipeline, metric=metric, target=target)
        self._nf.start()
        return {"started": True, "metric": metric, "target": target}

    def get_neurofeedback_score(self) -> dict:
        nf = self._nf
        if nf is None:
            return {"error": "no neurofeedback session — call start_neurofeedback first"}
        nf.sample()
        return nf.score()
