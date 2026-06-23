from bci_mcp.dsp.metrics import METRIC_NAMES, raw_metrics


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
