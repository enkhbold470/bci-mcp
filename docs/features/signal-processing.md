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

Band powers are computed via **Welch PSD** (`scipy.signal.welch`) and integrated with the trapezoid rule. Result is mean absolute power across channels, in µV².

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

Heuristic ratios derived from band powers (unscaled, then personalized by calibration):

| Metric | Formula | Interpretation |
|---|---|---|
| `focus` | β / (α + θ) | Concentration (high beta relative to alpha+theta) |
| `calm` | α / (α + β) | Relaxation (high alpha relative to beta) |
| `attention` | β / θ | Beta vs theta |
| `engagement` | (β + γ) / (α + θ + δ) | Pope-style engagement index |
| `fatigue` | (θ + δ) / (α + β) | Drowsiness (slow waves dominating) |
| `meditation` | θ / total | Relative theta power |

All metrics are then passed through `Calibration.apply()` which rescales using a personal baseline (min/max from the calibration recording).

## Signal quality (`bci_mcp.dsp.quality`)

`assess_quality(data, fs)` returns `(score: float, label: str, artifacts: list[str])`:

- **no_contact**: variance < 0.001 — electrode not making contact.
- **railing**: peak-to-peak > 2000 µV — signal is clipping. Score −0.6.
- **blink**: peak amplitude > 150 µV on channel 0 without railing. Added to artifact list.
- Label: `good` (score > 0.75), `fair` (> 0.4), `poor` (≤ 0.4).

## Calibration (`bci_mcp.dsp.calibration`)

`Calibration.from_samples(samples)` computes per-metric min/max from a baseline recording, then `apply(raw)` rescales each metric to 0–1 relative to that baseline. Without calibration, raw ratios are still useful but not normalized.