import numpy as np

from bci_mcp.devices.synthetic import SyntheticDevice


def test_shape_and_units():
    dev = SyntheticDevice(channels=4, sample_rate=256.0, chunk_samples=32, seed=1)
    dev.connect()
    dev.start()
    chunk = dev.read()
    assert chunk is not None
    assert chunk.data.shape == (4, 32)
    assert chunk.data.dtype == np.float32
    assert chunk.timestamps.shape == (32,)
    assert dev.info.units == "uV"


def test_read_returns_none_when_stopped():
    dev = SyntheticDevice(seed=1)
    assert dev.read() is None  # not started


def test_deterministic_with_seed():
    a = SyntheticDevice(seed=42)
    a.start()
    b = SyntheticDevice(seed=42)
    b.start()
    assert np.array_equal(a.read().data, b.read().data)


def test_higher_focus_has_more_beta_relative_to_alpha():
    # Generate a few seconds and compare 20Hz (beta) vs 10Hz (alpha) content.
    def power_at(dev, freq):
        dev.start()
        sig = np.concatenate([dev.read().data[0] for _ in range(40)])  # ~5s @256/32
        fft = np.abs(np.fft.rfft(sig))
        freqs = np.fft.rfftfreq(sig.size, 1 / dev.info.sample_rate)
        return fft[np.argmin(np.abs(freqs - freq))]

    low = SyntheticDevice(focus=0.0, seed=7)
    high = SyntheticDevice(focus=1.0, seed=7)
    ratio_low = power_at(low, 20) / power_at(SyntheticDevice(focus=0.0, seed=7), 10)
    ratio_high = power_at(high, 20) / power_at(SyntheticDevice(focus=1.0, seed=7), 10)
    assert ratio_high > ratio_low
