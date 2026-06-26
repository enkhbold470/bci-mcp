"""Cognitive metrics derived from band powers.

These are **heuristic band-power ratios**, not validated clinical measurements.
Each one is a recognizable simplification of an index from the literature; the
``METRIC_INFO`` table below records the exact formula, the work it draws on, and
an honest caveat for every metric. Downstream consumers (CLI, dashboard,
MCP/LLM) should treat the values as proxies, weight them by the per-reading
``confidence`` the pipeline attaches, and never present them as ground-truth
cognitive states.

Design notes
------------
* ``focus`` uses the genuine Pope, Bogart & Bartolome (1995) engagement index
  ``β / (α + θ)`` — the best-validated of these ratios.
* ``engagement`` is a *distinct* arousal ratio ``β / α`` (not the Pope index),
  so the two are not duplicates.
* Delta and gamma are intentionally **excluded** from every metric: on consumer
  hardware over short windows, 30-45 Hz "gamma" is dominated by EMG and <1-4 Hz
  delta by drift/ocular artifact, so building user-facing metrics on them adds
  noise, not signal. They are still reported as raw band powers.
* The metrics are chosen so no two are collinear on the same band in the same
  direction — in particular ``meditation`` *falls* with theta while ``fatigue``
  *rises* with it, so a drowsy reading cannot score high on both (a relative-
  theta "meditation" metric would have confounded the two).

References
----------
* Pope, Bogart & Bartolome (1995), *Biological Psychology* — engagement index
  ``β / (α + θ)``.
* Lubar (1991); Monastra et al. (1999), *Neuropsychology* — theta/beta ratio
  (TBR) for attention/ADHD; diagnostic validity later contested
  (Arns et al. 2013).
* Eoh, Chung & Kim (2005), *Int. J. Industrial Ergonomics* — ``(θ + α) / β`` as
  a driver mental-fatigue index.
* Berger (1929); NeuroSky eSense — alpha as the canonical relaxed-wakefulness
  rhythm underlying consumer calm/meditation meters.
"""
from __future__ import annotations

METRIC_NAMES = ("focus", "calm", "attention", "engagement", "fatigue", "meditation")
_EPS = 1e-9

# Metrics whose raw ratio is a fraction of a sum and therefore mathematically
# bounded to [0, 1] (rather than an unbounded a/b ratio). They need a different
# uncalibrated default mapping — see DEFAULT_SCALING.
BOUNDED_METRICS = frozenset({"calm", "meditation"})

# Uncalibrated default mapping: each raw ratio becomes a 0..1 score via
# ``sigmoid((value - center) / scale)``. Unbounded ratio metrics are neutral at
# 1.0 (numerator balances denominator); bounded [0, 1] metrics are neutral at
# 0.5 with a tighter scale. Without per-metric centers the bounded metrics could
# never read "high" uncalibrated — a global center of 1.0 caps them at
# sigmoid(0)=0.5. Calibration overrides this with a personal z-score baseline.
DEFAULT_SCALING: dict[str, tuple[float, float]] = {
    "focus": (1.0, 1.0),
    "calm": (0.5, 0.2),
    "attention": (1.0, 1.0),
    "engagement": (1.0, 1.0),
    "fatigue": (1.0, 1.0),
    "meditation": (0.5, 0.2),
}

# Self-describing definitions, surfaced to the LLM via the MCP
# ``get_metric_definitions`` tool so a model never has to guess what a number
# means or how much to trust it.
METRIC_INFO: dict[str, dict[str, str]] = {
    "focus": {
        "formula": "beta / (alpha + theta)",
        "basis": "Pope et al. (1995) EEG engagement/concentration index — the "
                 "best-validated of these ratios.",
        "caveat": "A proxy for task engagement/concentration, not a direct "
                  "measurement of 'focus'.",
    },
    "calm": {
        "formula": "alpha / (alpha + beta)",
        "basis": "Alpha-up / beta-down is a long-standing relaxation correlate.",
        "caveat": "Resting alpha also tracks drowsiness and eyes-closed state, "
                  "so high 'calm' is not necessarily relaxed attention.",
    },
    "attention": {
        "formula": "beta / theta (inverse of the theta/beta ratio, TBR)",
        "basis": "TBR (Lubar 1991; Monastra 1999) is the classic inattention "
                 "marker.",
        "caveat": "TBR's diagnostic validity is contested (Arns et al. 2013) and "
                  "it is a between-subjects trait marker, not a moment-to-moment "
                  "readout.",
    },
    "engagement": {
        "formula": "beta / alpha",
        "basis": "Beta/alpha arousal–activation ratio.",
        "caveat": "An arousal proxy, distinct from the Pope engagement index "
                  "(that formula is used by 'focus').",
    },
    "fatigue": {
        "formula": "(theta + alpha) / beta",
        "basis": "Eoh et al. (2005) driver mental-fatigue / drowsiness index.",
        "caveat": "Slow-wave dominance is ambiguous; corroborate with low "
                  "engagement before concluding fatigue.",
    },
    "meditation": {
        "formula": "alpha / (alpha + beta + theta)",
        "basis": "Relative alpha as a relaxed-wakefulness proxy (Berger rhythm; "
                 "NeuroSky eSense convention).",
        "caveat": "NOT a validated meditation classifier. Deliberately falls "
                  "with theta so it does not collapse into the drowsiness signal "
                  "the way a relative-theta metric would.",
    },
}


def raw_metrics(bp: dict[str, float]) -> dict[str, float]:
    """Unscaled metric ratios. Calibration maps these into 0..1 later.

    See the module docstring and ``METRIC_INFO`` for the basis and caveats of
    each metric. Only theta/alpha/beta are used; delta and gamma are excluded
    on purpose (drift- and EMG-dominated on consumer hardware).
    """
    t, a, b = bp["theta"], bp["alpha"], bp["beta"]
    return {
        "focus": b / (a + t + _EPS),            # Pope (1995) engagement index
        "calm": a / (a + b + _EPS),             # alpha vs beta relaxation
        "attention": b / (t + _EPS),            # inverse theta/beta ratio (TBR)
        "engagement": b / (a + _EPS),           # beta/alpha arousal ratio
        "fatigue": (t + a) / (b + _EPS),        # Eoh (2005) fatigue index
        "meditation": a / (a + b + t + _EPS),   # relative alpha (calm wakefulness)
    }
