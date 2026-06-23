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
    def __init__(self, device: Device | str, window_seconds: float = 1.0,
                 notch_freq: float = 60.0) -> None:
        self.device = create_device(device) if isinstance(device, str) else device
        self.stream = Stream(self.device)
        self.window = int(self.device.info.sample_rate * window_seconds)
        self.notch_freq = notch_freq
        self.calibration = Calibration()

    def start(self) -> None:
        self.stream.start()

    def stop(self) -> None:
        self.stream.stop()

    def _raw_metrics_now(self):
        fs = self.device.info.sample_rate
        data = self.stream.latest(self.window)
        if data.shape[1] < max(int(fs * 0.5), 64):
            return None, None, data, fs
        filtered = filters.bandpass(data, fs)
        filtered = filters.notch(filtered, fs, self.notch_freq)
        bp = bands.band_powers(filtered, fs)
        return metrics_mod.raw_metrics(bp), bp, data, fs

    def current_state(self) -> BrainState | None:
        raw, bp, data, fs = self._raw_metrics_now()
        if raw is None:
            return None
        scaled = self.calibration.apply(raw)
        q_score, q_label, artifacts = quality_mod.assess_quality(data, fs)
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
            self.calibration = Calibration.from_samples(samples)
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
