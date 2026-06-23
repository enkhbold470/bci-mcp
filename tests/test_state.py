from bci_mcp.dsp.state import BrainState


def _state():
    return BrainState(
        timestamp=1.0,
        metrics={"focus": 0.7, "calm": 0.3},
        band_powers={"alpha": 1.0},
        relative_band_powers={"alpha": 1.0},
        signal_quality="good",
        quality_score=0.9,
        artifacts=[],
        channels=4,
        sample_rate=256.0,
        calibrated=True,
    )


def test_to_dict_roundtrips_fields():
    d = _state().to_dict()
    assert d["metrics"]["focus"] == 0.7
    assert d["signal_quality"] == "good"
    assert d["channels"] == 4


def test_summary_is_readable_string():
    s = _state().summary()
    assert "focus" in s.lower()
    assert "good" in s.lower()
