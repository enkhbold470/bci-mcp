# Changelog

## 0.2.0
### Signal-processing accuracy & honesty
- **Per-reading confidence.** Every `BrainState` now carries `confidence` (0..1),
  per-metric `metric_confidence`, and a `status` (`ok`/`warming_up`/`unreliable`),
  folding in signal quality, calibration, and window fill. Surfaced through the
  MCP `get_brain_state`, `get_signal_quality`, and `stream_summary` tools.
- **Artifact handling, not just detection.** Hard artifacts (`flatline`,
  `railing`) or `poor` signal mark a reading `unreliable` and collapse its
  confidence, so contaminated windows are never narrated as clean. Added an
  `emg` artifact flag for implausibly large amplitudes.
- **Re-grounded metrics.** `focus` is now documented as the genuine Pope et al.
  (1995) engagement index `β/(α+θ)`; `engagement` is a distinct `β/α` arousal
  ratio (no longer mislabeled "Pope-style"); `fatigue` uses the Eoh et al. (2005)
  `(θ+α)/β` index; `meditation` is relative alpha `α/(α+β+θ)` — decoupled from
  theta so it no longer confounds with drowsiness/`fatigue`. Delta and gamma are
  excluded from metrics (drift/EMG-dominated on consumer hardware). Each metric
  ships a formula + basis + caveat via the new `get_metric_definitions` MCP tool.
- **Calibration fix.** Bounded metrics (`calm`, `meditation`) are centered at 0.5
  uncalibrated instead of being capped low; unbounded ratios stay centered at 1.0.
- **DSP fixes.** Longer default analysis window (2 s) with Welch segment averaging
  for stable low-frequency band power; narrow-band single-bin integration no
  longer silently returns 0; notch is applied before the bandpass.

## 0.1.0
- Device-agnostic EEG acquisition: synthetic, NeuroFocus (serial + BLE), OpenBCI/Muse via BrainFlow, LSL, generic serial, recording playback.
- DSP pipeline: band powers (δ θ α β γ), focus/calm/attention/engagement/fatigue/meditation metrics, signal quality + artifacts, calibration.
- Real Model Context Protocol server (FastMCP, stdio) with tools, resources, and a prompt.
- CLI: devices, stream, record, play, neurofeedback, dashboard, serve.
- Recording (CSV/npz/EDF) + replay, neurofeedback trainer, LSL publisher, FastAPI web dashboard.
