"""Band power via Welch PSD."""
from __future__ import annotations

import numpy as np
from scipy.signal import welch

BANDS: dict[str, tuple[float, float]] = {
    "delta": (1.0, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 13.0),
    "beta": (13.0, 30.0),
    "gamma": (30.0, 45.0),
}


def band_powers(data: np.ndarray, fs: float) -> dict[str, float]:
    """Mean absolute power per band, averaged over channels (µV²)."""
    nperseg = min(data.shape[-1], int(fs))
    freqs, psd = welch(data, fs=fs, nperseg=nperseg)
    psd = np.atleast_2d(psd)
    out: dict[str, float] = {}
    for band, (lo, hi) in BANDS.items():
        mask = (freqs >= lo) & (freqs < hi)
        if not mask.any():
            out[band] = 0.0
        else:
            out[band] = float(np.mean(np.trapezoid(psd[:, mask], freqs[mask], axis=-1)))
    return out


def relative_band_powers(bp: dict[str, float]) -> dict[str, float]:
    total = sum(bp.values()) or 1.0
    return {k: v / total for k, v in bp.items()}
