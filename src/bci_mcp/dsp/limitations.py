"""Single source of truth for what this pipeline is — and is not.

Every surface that presents a metric (CLI, dashboard, MCP/LLM) pulls its
honesty text from here so the tool's scope is stated the same way everywhere.
The metrics are heuristic band-power ratios from a continuous, averaging
spectral estimator. That estimator has hard limits, and stating them plainly
is the point of this module: a reader (human or LLM) should never mistake the
output for clinical qEEG, event-level analysis, or a validated cognitive
readout.
"""
from __future__ import annotations

# What the pipeline actually does, in auditable numbers. These mirror the
# Pipeline / bands / filters defaults; they are descriptive, not a second
# configuration source.
ANALYSIS_METHOD: dict[str, object] = {
    "estimator": "Welch power spectral density (scipy.signal.welch)",
    "window_seconds": 2.0,          # Pipeline default analysis window
    "segment_seconds": 1.0,         # Welch nperseg target (~1 s)
    "overlap": "50%",
    "frequency_resolution_hz": 1.0,  # ~1 / segment_seconds
    "filters": "60 Hz notch (Q=30) then 1-45 Hz order-4 Butterworth, zero-phase",
    "band_edges_hz": {
        "delta": [1.0, 4.0], "theta": [4.0, 8.0], "alpha": [8.0, 13.0],
        "beta": [13.0, 30.0], "gamma": [30.0, 45.0],
    },
    "band_edges_note": "Conventional consumer-grade boundaries, not a tuned "
                       "clinical/qEEG montage.",
}

# Plain-English limitations. Ordered most-important first.
LIMITATIONS: list[str] = [
    "Transient-blind: Welch PSD averages power over the whole window, so "
    "event-level activity (ERPs, sleep spindles, K-complexes, short bursts, "
    "epileptiform spikes) is averaged out and cannot be detected. This is not "
    "a time-resolved / event-related tool.",
    "Not clinical: band edges and filtering are standard consumer-grade "
    "settings, not a qEEG or clinical-neurofeedback montage. Do not expect "
    "results to match a clinical rig.",
    "Metrics are heuristic proxies: focus/calm/attention/engagement/fatigue/"
    "meditation are band-power ratios from the literature, not validated "
    "measurements of those cognitive states. No two people map the same way "
    "without calibration.",
    "No source localization or connectivity: single-window band power only — "
    "no coherence, phase, per-region mapping, or spatial analysis.",
    "No feature extraction / indexing beyond band power: the LLM only ever "
    "sees the computed scalar metrics, never raw samples, so it cannot recover "
    "anything the band-power step discarded.",
    "Snapshot, not trend: each reading is one short window; it does not track "
    "slow drift, habituation, or session-level dynamics on its own.",
    "Consumer-grade signal handling: artifacts are flagged (blink/EMG/railing/"
    "flatline) and collapse confidence, but there is no ICA/regression artifact "
    "removal, so contaminated data is dropped, not cleaned.",
]

# One-liner for compact surfaces (inline in every metric reading, CLI footer).
SHORT_DISCLAIMER: str = (
    "Heuristic band-power proxies from Welch PSD, not clinical or event-level "
    "EEG. Transients (ERPs/spindles/bursts) are averaged out; weight by "
    "`confidence` and treat `status`=='unreliable' as untrustworthy."
)


def pipeline_limitations() -> dict:
    """Structured description of the pipeline's scope and limits."""
    return {
        "method": ANALYSIS_METHOD,
        "limitations": LIMITATIONS,
        "disclaimer": SHORT_DISCLAIMER,
        "intended_use": "Casual insight, demos, and band-power neurofeedback — "
                        "not medical, diagnostic, or research-grade EEG.",
    }
