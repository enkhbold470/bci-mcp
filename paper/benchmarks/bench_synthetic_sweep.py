"""Sanity check: do the metrics recover a known generator parameter?

The synthetic device trades 10 Hz alpha amplitude for 20 Hz beta amplitude as
its ``focus`` parameter goes 0 → 1. A correct band-power pipeline must report
``focus`` (β/(α+θ)) rising and ``calm`` (α/(α+β)) falling with it. This checks
the implementation end to end; it says nothing about physiology.
"""
from __future__ import annotations

import numpy as np
from _common import save
from _windows import state_for, synthetic_window
from scipy.stats import spearmanr

LEVELS = [round(x, 1) for x in np.linspace(0.0, 1.0, 11)]
WINDOWS = 50
FS = 256.0
METRICS = ("focus", "calm", "engagement", "attention", "fatigue", "meditation")


def main() -> None:
    rows, xs, ys = [], [], {m: [] for m in METRICS}
    for level in LEVELS:
        vals = {m: [] for m in METRICS}
        for i in range(WINDOWS):
            s = state_for(synthetic_window(seed=1000 * i + int(level * 10), focus=level), FS)
            for m in METRICS:
                vals[m].append(s.metrics[m])
                ys[m].append(s.metrics[m])
            xs.append(level)
        rows.append({"focus_param": level,
                     **{f"{m}_mean": float(np.mean(v)) for m, v in vals.items()},
                     **{f"{m}_sd": float(np.std(v)) for m, v in vals.items()}})
        print(f"focus={level:.1f}  focus_metric={np.mean(vals['focus']):.3f}  "
              f"calm={np.mean(vals['calm']):.3f}")
    rho = {m: float(spearmanr(xs, ys[m]).statistic) for m in METRICS}
    print("spearman rho:", {k: round(v, 3) for k, v in rho.items()})
    save("synthetic_sweep", {"windows_per_level": WINDOWS, "sample_rate": FS,
                             "calibrated": False, "levels": rows, "spearman_rho": rho})


if __name__ == "__main__":
    main()
