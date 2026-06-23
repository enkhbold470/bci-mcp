import numpy as np
from bci_mcp.dsp.bands import BANDS, band_powers, relative_band_powers


def test_alpha_sine_peaks_in_alpha_band():
    fs, n = 256.0, 1024
    t = np.arange(n) / fs
    data = np.tile(np.sin(2 * np.pi * 10 * t), (2, 1))  # 10 Hz = alpha
    bp = band_powers(data, fs)
    assert set(bp) == set(BANDS)
    assert bp["alpha"] == max(bp.values())


def test_relative_sums_to_one():
    fs, n = 256.0, 1024
    t = np.arange(n) / fs
    data = np.tile(np.sin(2 * np.pi * 10 * t) + np.sin(2 * np.pi * 20 * t), (1, 1))
    rel = relative_band_powers(band_powers(data, fs))
    assert abs(sum(rel.values()) - 1.0) < 1e-6
