import pytest

from bci_mcp.dsp.calibration import Calibration
from bci_mcp.dsp.metrics import DEFAULT_SCALING


def test_uncalibrated_maps_to_unit_interval():
    cal = Calibration()
    assert not cal.calibrated
    out = cal.apply({"focus": 1.0, "calm": 0.0})
    assert all(0.0 <= v <= 1.0 for v in out.values())


def test_bounded_metric_can_read_high_uncalibrated():
    # Regression: with the old global center=1.0, bounded [0,1] metrics like
    # meditation were capped near sigmoid(0)=0.5 and could never read "high".
    cal = Calibration(scaling=DEFAULT_SCALING)
    assert not cal.calibrated
    low = cal.apply({"meditation": 0.1})["meditation"]
    high = cal.apply({"meditation": 0.9})["meditation"]
    assert low < 0.3
    assert high > 0.7
    assert high > low


def test_extreme_ratio_does_not_overflow():
    cal = Calibration()
    out = cal.apply({"fatigue": 1e12, "attention": -1e12})
    assert all(0.0 <= v <= 1.0 for v in out.values())


def test_from_samples_centers_at_half():
    samples = [{"focus": x} for x in (0.8, 1.0, 1.2)]  # mean ~1.0
    cal = Calibration.from_samples(samples)
    assert cal.calibrated
    out = cal.apply({"focus": 1.0})
    assert abs(out["focus"] - 0.5) < 0.05


def test_json_roundtrip():
    cal = Calibration.from_samples([{"focus": 0.5}, {"focus": 1.5}])
    restored = Calibration.from_json(cal.to_json())
    assert restored.baseline == cal.baseline


def test_from_samples_empty_raises():
    with pytest.raises(ValueError):
        Calibration.from_samples([])
