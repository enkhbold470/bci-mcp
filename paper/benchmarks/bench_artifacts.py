"""Artifact flagging on injected, known artifacts (synthetic ground truth).

Each trial takes a clean synthetic 2 s window (4 ch @ 256 Hz), optionally
injects one artifact of known amplitude, and runs the full pipeline. We report
how often the intended flag fires, how often the reading is marked
``unreliable``, and the false-flag rate on clean windows. Thresholds in
``dsp/quality.py`` are fixed heuristics; these rates are properties of those
thresholds on this signal, not of any real headset.
"""
from __future__ import annotations

import numpy as np
from _common import save
from _windows import state_for, synthetic_window
from scipy.signal import butter, filtfilt

FS = 256.0
N = 300


def blink(w: np.ndarray, amp: float, rng) -> np.ndarray:
    w = w.copy()
    n = w.shape[1]
    t = np.arange(n) / FS
    c = rng.uniform(0.4, 1.6)
    bump = amp * np.exp(-0.5 * ((t - c) / 0.08) ** 2)  # ~200 ms ocular blink
    w[0] += bump
    if w.shape[0] > 1:
        w[1] += 0.6 * bump
    return w


def emg(w: np.ndarray, amp: float, rng) -> np.ndarray:
    b, a = butter(4, [30 / (FS / 2), 100 / (FS / 2)], btype="band")
    noise = filtfilt(b, a, rng.normal(0, 1, w.shape), axis=-1)
    noise *= amp / np.std(noise)
    return w + noise


def railing(w: np.ndarray, amp: float, rng) -> np.ndarray:
    t = np.arange(w.shape[1]) / FS
    return w + amp * np.sign(np.sin(2 * np.pi * rng.uniform(0.5, 2.0) * t))


def flatline(w: np.ndarray, amp: float, rng) -> np.ndarray:
    return np.full_like(w, rng.uniform(-3000, 3000))  # lead-off: constant DC


CASES = [  # (name, injector, amplitudes µV, expected flag)
    ("blink", blink, [50, 100, 150, 200, 300, 400], "blink"),
    ("emg", emg, [10, 25, 50, 75, 100, 150], "emg"),
    ("railing", railing, [500, 800, 1000, 1500], "railing"),
    ("flatline", flatline, [0], "flatline"),
]


def main() -> None:
    rng = np.random.default_rng(7)
    clean_flags, clean_unrel = 0, 0
    for i in range(N):
        s = state_for(synthetic_window(seed=i), FS)
        clean_flags += bool(s.artifacts)
        clean_unrel += s.status == "unreliable"
    print(f"clean: any flag {clean_flags}/{N}, unreliable {clean_unrel}/{N}")

    rows = []
    for name, fn, amps, flag in CASES:
        for amp in amps:
            hit = unrel = 0
            conf = []
            for i in range(N):
                s = state_for(fn(synthetic_window(seed=10_000 + i), amp, rng), FS)
                hit += flag in s.artifacts
                unrel += s.status == "unreliable"
                conf.append(s.confidence)
            rows.append({"artifact": name, "amplitude_uv": amp, "trials": N,
                         "flag_rate": hit / N, "unreliable_rate": unrel / N,
                         "median_confidence": float(np.median(conf))})
            print(f"{name:9s} {amp:6g} µV  flagged {hit / N:5.1%}  "
                  f"unreliable {unrel / N:5.1%}  conf {np.median(conf):.2f}")
    save("artifacts", {"trials_per_cell": N, "sample_rate": FS, "channels": 4,
                       "clean": {"trials": N, "any_flag_rate": clean_flags / N,
                                 "unreliable_rate": clean_unrel / N},
                       "injected": rows})


if __name__ == "__main__":
    main()
