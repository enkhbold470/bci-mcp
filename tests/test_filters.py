import numpy as np

from bci_mcp.dsp.filters import bandpass, notch


def _sine(freq, fs, n, ch=1):
    t = np.arange(n) / fs
    return np.tile(np.sin(2 * np.pi * freq * t), (ch, 1))


def test_bandpass_attenuates_out_of_band():
    fs, n = 256.0, 1024
    in_band = _sine(10, fs, n)
    out_band = _sine(70, fs, n)
    assert np.std(bandpass(in_band, fs)) > 0.5 * np.std(in_band)
    assert np.std(bandpass(out_band, fs)) < 0.2 * np.std(out_band)


def test_notch_removes_line_noise():
    fs, n = 256.0, 1024
    sig = _sine(10, fs, n) + _sine(60, fs, n)
    filtered = notch(sig, fs, freq=60.0)
    fft = np.abs(np.fft.rfft(filtered[0]))
    freqs = np.fft.rfftfreq(n, 1 / fs)
    p60 = fft[np.argmin(np.abs(freqs - 60))]
    p10 = fft[np.argmin(np.abs(freqs - 10))]
    assert p60 < 0.1 * p10


def test_notch_above_nyquist_returns_input():
    data = _sine(10, 100.0, 64)
    out = notch(data, fs=100.0, freq=60.0)  # 60 Hz >= Nyquist (50 Hz)
    assert np.array_equal(out, data)
