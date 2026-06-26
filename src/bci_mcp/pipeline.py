"""Pipeline: ties a Device/Stream to the DSP chain and emits BrainState."""
from __future__ import annotations

import time

from .core.device import Device
from .core.registry import create_device
from .core.stream import Stream
from .dsp import bands, filters
from .dsp import metrics as metrics_mod
from .dsp import quality as quality_mod
from .dsp.calibration import Calibration
from .dsp.state import BrainState


class Pipeline:
    def __init__(self, device: Device | str, window_seconds: float = 2.0,
                 notch_freq: float = 60.0) -> None:
        self.device = create_device(device) if isinstance(device, str) else device
        self.stream = Stream(self.device)
        # ~2 s gives Welch enough segments to resolve the low-frequency
        # (delta/theta) bands that several metrics depend on, instead of a single
        # noisy 1 s periodogram.
        self.window = int(self.device.info.sample_rate * window_seconds)
        self.notch_freq = notch_freq
        self.calibration = Calibration(scaling=metrics_mod.DEFAULT_SCALING)

    def start(self) -> None:
        self.stream.start()

    def stop(self) -> None:
        self.stream.stop()

    def _raw_metrics_now(self):
        fs = self.device.info.sample_rate
        data = self.stream.latest(self.window)
        if data.shape[1] < max(int(fs * 0.5), 64):
            return None, None, data, fs
        # Notch first (remove line noise before it can fold into the passband),
        # then bandpass to the 1-45 Hz analysis range.
        filtered = filters.notch(data, fs, self.notch_freq)
        filtered = filters.bandpass(filtered, fs)
        bp = bands.band_powers(filtered, fs)
        return metrics_mod.raw_metrics(bp), bp, data, fs

    def _confidence(self, quality_score: float, samples: int) -> float:
        """How much to trust a reading: signal quality × calibration × window fill."""
        fill = min(1.0, samples / float(self.window)) if self.window else 1.0
        cal_factor = 1.0 if self.calibration.calibrated else 0.6
        return float(max(0.0, min(1.0, quality_score * cal_factor * fill)))

    def current_state(self) -> BrainState | None:
        raw, bp, data, fs = self._raw_metrics_now()
        if raw is None:
            return None
        scaled = self.calibration.apply(raw)
        q_score, q_label, artifacts = quality_mod.assess_quality(data, fs)
        confidence = self._confidence(q_score, int(data.shape[1]))
        # Artifact handling, not just detection: a hard artifact or poor signal
        # flags the reading unreliable and collapses its confidence, so the
        # metrics are never narrated as a clean reading.
        hard = any(a in quality_mod.HARD_ARTIFACTS for a in artifacts)
        status = "unreliable" if (hard or q_label == "poor") else "ok"
        if status == "unreliable":
            confidence = min(confidence, 0.1)
        confidence = round(confidence, 4)
        return BrainState(
            timestamp=time.time(),
            metrics=scaled,
            band_powers=bp,
            relative_band_powers=bands.relative_band_powers(bp),
            signal_quality=q_label,
            quality_score=q_score,
            artifacts=artifacts,
            channels=self.device.info.channel_count,
            sample_rate=fs,
            calibrated=self.calibration.calibrated,
            confidence=confidence,
            metric_confidence={k: confidence for k in scaled},
            status=status,
        )

    def calibrate(self, seconds: float = 20.0) -> Calibration:
        samples = []
        end = time.time() + seconds
        while time.time() < end:
            raw, _, _, _ = self._raw_metrics_now()
            if raw is not None:
                samples.append(raw)
            time.sleep(0.25)
        if samples:
            self.calibration = Calibration.from_samples(
                samples, scaling=metrics_mod.DEFAULT_SCALING)
        return self.calibration

    def record(self, seconds: float, path: str, fmt: str | None = None) -> str:
        from .recording.recorder import Recorder
        from .recording.writer import save_recording

        recorder = Recorder()
        self.stream.add_consumer(recorder)
        recorder.start()
        try:
            time.sleep(seconds)
        finally:
            recorder.stop()
            self.stream.remove_consumer(recorder)
        data = recorder.data()
        return save_recording(
            data, self.device.info.sample_rate, self.device.info.channel_names, path, fmt,
            metadata={"device": self.device.info.name, "uri": self.device.info.uri},
        )
