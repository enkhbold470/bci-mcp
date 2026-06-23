from bci_mcp.dsp.calibration import Calibration


def test_uncalibrated_maps_to_unit_interval():
    cal = Calibration()
    assert not cal.calibrated
    out = cal.apply({"focus": 1.0, "calm": 0.0})
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
