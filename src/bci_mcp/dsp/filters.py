"""Zero-phase EEG filters (operate along the last axis: (channels, n_samples))."""
from __future__ import annotations

import numpy as np
from scipy.signal import butter, filtfilt, iirnotch


def bandpass(data: np.ndarray, fs: float, low: float = 1.0, high: float = 45.0,
             order: int = 4) -> np.ndarray:
    nyq = 0.5 * fs
    b, a = butter(order, [low / nyq, min(high, nyq - 1) / nyq], btype="band")
    return filtfilt(b, a, data, axis=-1)


def notch(data: np.ndarray, fs: float, freq: float = 60.0, q: float = 30.0) -> np.ndarray:
    b, a = iirnotch(freq / (0.5 * fs), q)
    return filtfilt(b, a, data, axis=-1)
