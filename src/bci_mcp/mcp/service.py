"""Testable brain-service core. server.py adapts this to MCP."""
from __future__ import annotations

import math
import threading
import time
from collections import deque

from ..pipeline import Pipeline
from ..recording.paths import safe_record_path, validate_mcp_uri

# Untrusted MCP clients drive this service, so every argument is bounded:
# durations are capped (the singleton blocks while recording/calibrating),
# stored labels/events are capped (memory), and formats are allow-listed.
MAX_RECORD_SECONDS = 3600.0
MAX_CALIBRATE_SECONDS = 300.0
MAX_LABEL_CHARS = 512
MAX_EVENTS = 1000
RECORD_FORMATS = ("npz", "csv", "edf")


def _seconds_error(seconds: object, maximum: float) -> str | None:
    try:
        value = float(seconds)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return f"seconds must be a number, got {seconds!r}"
    if not math.isfinite(value) or value <= 0:
        return f"seconds must be a positive finite number, got {seconds!r}"
    if value > maximum:
        return f"seconds must be <= {maximum:g}, got {value:g}"
    return None


class BrainService:
    def __init__(self) -> None:
        self._pipeline: Pipeline | None = None
        self._events: deque[dict] = deque(maxlen=MAX_EVENTS)
        self._nf = None
        self._lock = threading.Lock()

    def list_devices(self) -> dict:
        from ..core.registry import discover, list_schemes

        return {"devices": discover(), "schemes": list_schemes()}

    def connect(self, device_uri: str = "synthetic://") -> dict:
        try:
            validate_mcp_uri(device_uri)
        except ValueError as exc:
            return {"error": str(exc)}
        with self._lock:
            if self._pipeline is not None:
                self._pipeline.stop()
                self._pipeline = None
                self._nf = None
            try:
                pipeline = Pipeline(device_uri)
                pipeline.start()
            except Exception as exc:  # unknown board, bad params, missing extra…
                return {"error": f"could not connect to '{device_uri}': {exc}"}
            self._pipeline = pipeline
            return {"connected": True, "device": pipeline.device.info.name,
                    "uri": device_uri}

    def disconnect(self) -> dict:
        with self._lock:
            if self._pipeline is not None:
                self._pipeline.stop()
                self._pipeline = None
            self._nf = None
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
        err = _seconds_error(seconds, MAX_CALIBRATE_SECONDS)
        if err is not None:
            return {"error": err}
        if len(condition) > MAX_LABEL_CHARS:
            return {"error": f"condition must be <= {MAX_LABEL_CHARS} characters"}
        cal = self._pipeline.calibrate(seconds=float(seconds))
        return {"calibrated": cal.calibrated, "condition": condition,
                "metrics": list(cal.baseline)}

    def mark_event(self, label: str) -> dict:
        if len(label) > MAX_LABEL_CHARS:
            return {"error": f"label must be <= {MAX_LABEL_CHARS} characters"}
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
        err = _seconds_error(seconds, MAX_RECORD_SECONDS)
        if err is not None:
            return {"error": err}
        effective_fmt = (fmt or str(path).rsplit(".", 1)[-1]).lower()
        if effective_fmt not in RECORD_FORMATS:
            return {"error": f"unsupported recording format '{effective_fmt}' — "
                             f"use one of: {', '.join(RECORD_FORMATS)}"}
        try:
            safe_path = safe_record_path(path)
        except ValueError as exc:
            return {"error": str(exc)}
        try:
            out = self._pipeline.record(seconds=float(seconds), path=safe_path, fmt=fmt)
        except Exception as exc:  # e.g. missing optional writer backend (pyedflib)
            return {"error": f"recording failed: {exc}"}
        return {"recorded": True, "path": out, "seconds": float(seconds)}

    def start_neurofeedback(self, metric: str = "focus", target: float = 0.7) -> dict:
        if self._pipeline is None:
            return {"error": "not connected"}
        from ..dsp.metrics import METRIC_INFO

        if metric not in METRIC_INFO:
            return {"error": f"unknown metric '{metric}' — "
                             f"use one of: {', '.join(sorted(METRIC_INFO))}"}
        try:
            target = float(target)
        except (TypeError, ValueError):
            return {"error": f"target must be a number, got {target!r}"}
        if not math.isfinite(target):
            return {"error": "target must be a finite number"}
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
