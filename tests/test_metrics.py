from bci_mcp.dsp.metrics import (
    BOUNDED_METRICS,
    DEFAULT_SCALING,
    METRIC_INFO,
    METRIC_NAMES,
    raw_metrics,
)


def test_all_metrics_present():
    bp = {"delta": 1, "theta": 1, "alpha": 1, "beta": 1, "gamma": 1}
    m = raw_metrics(bp)
    assert set(m) == set(METRIC_NAMES)


def test_more_beta_raises_focus():
    low = raw_metrics({"delta": 1, "theta": 2, "alpha": 2, "beta": 1, "gamma": 1})
    high = raw_metrics({"delta": 1, "theta": 2, "alpha": 2, "beta": 8, "gamma": 1})
    assert high["focus"] > low["focus"]


def test_more_alpha_raises_calm():
    low = raw_metrics({"delta": 1, "theta": 1, "alpha": 1, "beta": 5, "gamma": 1})
    high = raw_metrics({"delta": 1, "theta": 1, "alpha": 9, "beta": 5, "gamma": 1})
    assert high["calm"] > low["calm"]


def test_engagement_is_beta_over_alpha():
    m = raw_metrics({"delta": 1, "theta": 1, "alpha": 2, "beta": 6, "gamma": 1})
    assert abs(m["engagement"] - 6 / 2) < 1e-6


def test_meditation_falls_with_theta_while_fatigue_rises():
    # meditation must NOT be collinear with fatigue on theta: more theta should
    # lower meditation (decoupled from drowsiness) while raising fatigue.
    low_theta = raw_metrics({"delta": 1, "theta": 1, "alpha": 5, "beta": 3, "gamma": 1})
    high_theta = raw_metrics({"delta": 1, "theta": 9, "alpha": 5, "beta": 3, "gamma": 1})
    assert high_theta["meditation"] < low_theta["meditation"]
    assert high_theta["fatigue"] > low_theta["fatigue"]


def test_metrics_exclude_delta_and_gamma():
    base = {"delta": 1, "theta": 2, "alpha": 3, "beta": 4, "gamma": 5}
    bumped = {**base, "delta": 100, "gamma": 100}
    assert raw_metrics(base) == raw_metrics(bumped)


def test_info_and_scaling_cover_all_metrics():
    assert set(METRIC_INFO) == set(METRIC_NAMES)
    assert set(DEFAULT_SCALING) == set(METRIC_NAMES)
    assert BOUNDED_METRICS <= set(METRIC_NAMES)
    for info in METRIC_INFO.values():
        assert {"formula", "basis", "caveat"} <= set(info)
