from bci_mcp.neurofeedback.trainer import NeurofeedbackSession


class FakePipeline:
    """Feeds scripted metric values without threads."""

    def __init__(self, values):
        self._values = list(values)

    def current_state(self):
        from bci_mcp.dsp.state import BrainState

        if not self._values:
            return None
        v = self._values.pop(0)
        return BrainState(timestamp=0.0, metrics={"focus": v}, band_powers={},
                          relative_band_powers={}, signal_quality="good",
                          quality_score=1.0, artifacts=[], channels=1,
                          sample_rate=256.0, calibrated=False)


def test_score_counts_time_in_zone():
    pipe = FakePipeline([0.9, 0.2, 0.8, 0.85, 0.1])
    sess = NeurofeedbackSession(pipe, metric="focus", target=0.7)
    sess.start()
    for _ in range(5):
        sess.sample()
    summary = sess.summary()
    # 3 of 5 samples >= 0.7
    assert summary.samples == 5
    assert abs(summary.time_in_zone_pct - 60.0) < 1e-6
    assert 0.0 <= summary.mean_score <= 1.0


def test_score_dict_shape():
    pipe = FakePipeline([0.8])
    sess = NeurofeedbackSession(pipe, metric="focus", target=0.7)
    sess.start()
    sess.sample()
    score = sess.score()
    assert "in_zone" in score and "cumulative_in_zone_pct" in score
    assert score["in_zone"] is True
