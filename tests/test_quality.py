import numpy as np

from bci_mcp.dsp.quality import HARD_ARTIFACTS, assess_quality


def test_flatline_is_no_contact():
    data = np.zeros((1, 256), dtype=np.float32)
    score, label, artifacts = assess_quality(data, 256.0)
    assert label == "no_contact"
    assert score == 0.0
    assert "flatline" in artifacts


def test_good_eeg_amplitude():
    rng = np.random.default_rng(0)
    data = rng.normal(0, 20.0, (1, 256)).astype(np.float32)  # ~20µV noise
    score, label, _ = assess_quality(data, 256.0)
    assert label == "good"
    assert score > 0.75


def test_railing_flagged():
    data = np.full((1, 256), 5000.0, dtype=np.float32)
    data[0, ::2] = -5000.0  # huge swing, not flat
    _, _, artifacts = assess_quality(data, 256.0)
    assert "railing" in artifacts


def test_emg_flagged_for_large_amplitude():
    rng = np.random.default_rng(1)
    data = rng.normal(0, 150.0, (1, 256)).astype(np.float32)  # peak-to-peak ~400-2000µV
    score, _, artifacts = assess_quality(data, 256.0)
    assert "emg" in artifacts
    assert score < 1.0


def test_hard_artifacts_are_flatline_and_railing():
    assert "flatline" in HARD_ARTIFACTS
    assert "railing" in HARD_ARTIFACTS
    assert "blink" not in HARD_ARTIFACTS
