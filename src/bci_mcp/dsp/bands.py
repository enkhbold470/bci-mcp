"""Band power via Welch PSD.

Band power is the integral of the Welch power spectral density over each band
(scipy ``welch`` + trapezoid). This is the standard EEG band-power estimator; by
Parseval it equals the variance (RMS²) of the band-filtered signal up to scaling,
so the choice of "PSD vs RMS" is a unit convention, not a correctness question.

Two practical details handled here:

* **Welch averaging.** ``nperseg`` targets ~1 s segments with 50% overlap, so a
  longer analysis window is averaged over several segments (lower-variance PSD)
  instead of returning a single noisy periodogram.
* **Narrow-band guard.** ``trapezoid`` over a single frequency bin returns 0. At
  coarse resolution a narrow band (e.g. gamma at a low sample rate) can capture
  just one bin, which would silently zero that band's power; we fall back to
  rectangular integration in that case.
"""
from __future__ import annotations

import numpy as np
from scipy.integrate import trapezoid
from scipy.signal import welch

BANDS: dict[str, tuple[float, float]] = {
    # Conventional consumer-grade boundaries. Note that EEG band edges are not
    # universally fixed; theta/alpha/beta match the textbook values and
    # delta(1-4)/gamma(30-45) are common variants (the 45 Hz ceiling keeps
    # gamma below 50/60 Hz mains noise on consumer hardware).
    "delta": (1.0, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 13.0),
    "beta": (13.0, 30.0),
    "gamma": (30.0, 45.0),
}


def band_powers(data: np.ndarray, fs: float, nperseg: int | None = None) -> dict[str, float]:
    """Mean absolute power per band, averaged over channels (µV²)."""
    data = np.atleast_2d(data)
    n = data.shape[-1]
    if nperseg is None:
        # ~1 s segments → Welch averages multiple segments when the window is
        # longer, reducing variance; falls back to one segment for short windows.
        nperseg = int(min(n, max(fs, 1.0)))
    nperseg = max(1, min(int(nperseg), n))
    freqs, psd = welch(data, fs=fs, nperseg=nperseg, noverlap=nperseg // 2)
    psd = np.atleast_2d(psd)
    df = float(freqs[1] - freqs[0]) if len(freqs) > 1 else 1.0
    out: dict[str, float] = {}
    for band, (lo, hi) in BANDS.items():
        mask = (freqs >= lo) & (freqs < hi)
        nbins = int(np.count_nonzero(mask))
        if nbins == 0:
            out[band] = 0.0
        elif nbins == 1:
            # trapezoid over a single sample is 0 — use rectangular integration.
            out[band] = float(np.mean(psd[:, mask].sum(axis=-1)) * df)
        else:
            out[band] = float(np.mean(trapezoid(psd[:, mask], freqs[mask], axis=-1)))
    return out


def relative_band_powers(bp: dict[str, float]) -> dict[str, float]:
    total = sum(bp.values()) or 1.0
    return {k: v / total for k, v in bp.items()}
