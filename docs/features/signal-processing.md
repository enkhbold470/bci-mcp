# Signal Processing

The DSP pipeline in `bci_mcp.dsp` converts raw multi-channel EEG (µV) into interpretable cognitive metrics.

## Filters (`bci_mcp.dsp.filters`)

All filters are zero-phase (using `scipy.signal.filtfilt`) and operate on `(channels, n_samples)` arrays.

### Bandpass filter

1–45 Hz 4th-order Butterworth, applied before all other processing:

```python
from bci_mcp.dsp.filters import bandpass, notch
filtered = bandpass(data, fs=256.0)          # 1–45 Hz
filtered = bandpass(data, fs=256.0, low=8, high=13)  # alpha only
```

### Notch filter

Removes power-line interference (default 60 Hz; use 50 Hz in Europe):

```python
clean = notch(filtered, fs=256.0, freq=60.0, q=30.0)
```

## Band powers (`bci_mcp.dsp.bands`)

Band powers are computed via **Welch PSD** (`scipy.signal.welch`) and integrated with the trapezoid rule. Result is mean absolute power across channels, in µV². By Parseval's theorem this integrated-PSD band power equals the variance (RMS²) of the band-filtered signal up to scaling, so "PSD vs RMS" is a unit convention, not a correctness choice.

`band_powers` targets ~1 s Welch segments with 50 % overlap so a longer analysis window is averaged over several segments (lower-variance PSD) rather than a single noisy periodogram, and it falls back to rectangular integration for any band that captures only one frequency bin (a single-bin trapezoid would otherwise return 0).

EEG band edges are not universally fixed; `theta`/`alpha`/`beta` use textbook values and `delta` (1–4 Hz) / `gamma` (30–45 Hz) are common variants. The 45 Hz gamma ceiling keeps it below 50/60 Hz mains noise on consumer hardware.

| Band | Frequency range |
|---|---|
| delta | 1–4 Hz |
| theta | 4–8 Hz |
| alpha | 8–13 Hz |
| beta | 13–30 Hz |
| gamma | 30–45 Hz |

```python
from bci_mcp.dsp.bands import band_powers, relative_band_powers
bp = band_powers(filtered, fs=256.0)
# {"delta": 12.3, "theta": 5.6, "alpha": 18.4, "beta": 9.1, "gamma": 2.2}

rbp = relative_band_powers(bp)
# {"delta": 0.26, "theta": 0.12, "alpha": 0.39, "beta": 0.19, "gamma": 0.05}
```

## Cognitive metrics (`bci_mcp.dsp.metrics`)

**Heuristic band-power ratios, not validated clinical measurements.** Each is a recognizable simplification of an index from the literature; `metrics.METRIC_INFO` (also exposed via the MCP `get_metric_definitions` tool) records the formula, basis, and an honest caveat for each.

| Metric | Formula | Basis (see `METRIC_INFO` for caveats) |
|---|---|---|
| `focus` | β / (α + θ) | Pope et al. (1995) EEG engagement index — best-validated of these ratios |
| `calm` | α / (α + β) | Alpha-up / beta-down relaxation correlate |
| `attention` | β / θ | Inverse theta/beta ratio (TBR; Lubar 1991, Monastra 1999; validity contested) |
| `engagement` | β / α | Beta/alpha arousal–activation ratio (distinct from the Pope index) |
| `fatigue` | (θ + α) / β | Eoh et al. (2005) driver mental-fatigue index |
| `meditation` | α / (α + β + θ) | Relative alpha (Berger rhythm / NeuroSky convention) |

Delta and gamma are deliberately **excluded** from every metric: on consumer hardware over short windows, 30–45 Hz "gamma" is dominated by EMG and <1–4 Hz delta by drift, so they would add noise rather than signal (they remain available as raw band powers). The metrics are also chosen so no two are collinear on the same band in the same direction — `meditation` *falls* with theta while `fatigue` *rises* with it, so a drowsy reading cannot score high on both.

All metrics are then passed through `Calibration.apply()`, which rescales each to 0–1. With a personal baseline it uses a per-metric z-score; **uncalibrated**, it uses a per-metric default center (bounded metrics like `calm`/`meditation` are centered at 0.5, unbounded ratios at 1.0) so bounded metrics can still read high without calibration.

## Limitations (`bci_mcp.dsp.limitations`)

The estimator has hard limits, and the package states them the same way everywhere from a single source of truth (`dsp/limitations.py`):

- **Transient-blind.** Welch PSD averages power over the whole window, so event-level activity (ERPs, sleep spindles, K-complexes, short bursts, epileptiform spikes) is averaged out and cannot be detected. This is not a time-resolved / event-related tool — that would need epoching plus time-frequency analysis upstream.
- **Not clinical.** Band edges and filtering are standard consumer-grade settings, not a qEEG or clinical-neurofeedback montage.
- **Proxies, not measurements.** The metrics are band-power ratios from the literature, not validated readouts of the named cognitive states.
- **No source localization / connectivity**, and the LLM only ever sees the computed scalar metrics — never raw samples — so it cannot recover anything the band-power step discarded.

These are surfaced to consumers via the `get_pipeline_limitations` and `get_metric_definitions` MCP tools, an inline `disclaimer` on every reading, the CLI caveat line, and the dashboard banner / `GET /api/info`.

## Signal quality (`bci_mcp.dsp.quality`)

`assess_quality(data, fs)` returns `(score: float, label: str, artifacts: list[str])`:

- **no_contact / flatline**: variance < 0.001 — electrode not making contact.
- **railing**: peak-to-peak > 2000 µV — signal is clipping. Score −0.6.
- **emg**: peak-to-peak 400–2000 µV — implausibly large for scalp EEG, likely muscle. Score −0.25.
- **blink**: peak amplitude > 150 µV on channel 0 without railing. Added to artifact list.
- Label: `good` (score > 0.75), `fair` (> 0.4), `poor` (≤ 0.4).

`flatline` and `railing` are **hard artifacts** (`quality.HARD_ARTIFACTS`): the pipeline marks any reading containing one — or any `poor`-quality window — as `status = "unreliable"` and collapses its `confidence` so contaminated metrics are never narrated as a clean reading.

## Confidence (`Pipeline.current_state`)

Every `BrainState` carries a `confidence` (0..1) and per-metric `metric_confidence`, plus a `status` of `ok` / `warming_up` / `unreliable`. Confidence folds in signal quality, whether a baseline has been calibrated (×0.6 uncalibrated), and how full the analysis window was. The MCP `get_brain_state`, `get_signal_quality`, and `stream_summary` tools surface these so an LLM (or any consumer) can hedge or discard low-confidence readings.

## Calibration (`bci_mcp.dsp.calibration`)

`Calibration.from_samples(samples)` computes a per-metric mean/std from a baseline recording, then `apply(raw)` maps each metric to 0–1 via a logistic of its z-score relative to that baseline. Without calibration it uses the per-metric default centers in `metrics.DEFAULT_SCALING` (bounded metrics centered at 0.5, unbounded ratios at 1.0), so uncalibrated readings are still usable — just not personalized.