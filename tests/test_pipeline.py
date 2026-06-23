import time

from bci_mcp.dsp.state import BrainState
from bci_mcp.pipeline import Pipeline


def test_pipeline_produces_brainstate():
    p = Pipeline("synthetic://?seed=1", window_seconds=1.0)
    p.start()
    try:
        state = None
        for _ in range(50):  # poll up to ~5s for the buffer to fill
            time.sleep(0.1)
            state = p.current_state()
            if state is not None:
                break
        assert isinstance(state, BrainState)
        assert set(state.metrics)  # non-empty
        assert all(0.0 <= v <= 1.0 for v in state.metrics.values())
        assert state.channels == 4
    finally:
        p.stop()


def test_calibrate_sets_baseline():
    p = Pipeline("synthetic://?seed=2", window_seconds=1.0)
    p.start()
    try:
        time.sleep(1.2)
        cal = p.calibrate(seconds=1)
        assert cal.calibrated
        assert p.current_state().calibrated
    finally:
        p.stop()
