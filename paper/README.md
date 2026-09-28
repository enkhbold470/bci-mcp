# Paper and benchmarks

| Path | What it is |
|---|---|
| `paper.md`, `paper.bib` | Short software paper in the format of the *Journal of Open Source Software* (JOSS) |
| `preprint/main.tex` | Longer technical report for arXiv (build: `tectonic -X compile preprint/main.tex`) |
| `benchmarks/` | Scripts that produce every number in both papers |
| `results/` | JSON output of those scripts, including machine and package versions |
| `figures/` | Figures rendered from `results/` |

## Reproduce

```bash
pip install -e ".[all,dev]" matplotlib
cd paper/benchmarks
python bench_compute.py          # per-window DSP cost
python bench_synthetic_sweep.py  # metrics vs. a known generator parameter
python bench_artifacts.py        # injected-artifact flag rates
python bench_mcp_roundtrip.py    # stdio MCP latency (needs `bci-mcp` on PATH)

# Real EEG: PhysioNet EEG Motor Movement/Imagery Dataset, runs R01 (eyes open)
# and R02 (eyes closed) for subjects 1-109, about 280 MB.
mkdir -p data && cd data
for s in $(seq -f "%03g" 1 109); do for r in 01 02; do
  curl -sfLO "https://physionet.org/files/eegmmidb/1.0.0/S$s/S${s}R$r.edf"
done; done
cd .. && python bench_eyes_closed.py data

python make_figures.py
```

Timings depend on the machine; everything else is deterministic (fixed seeds).

## Data

Schalk, G., McFarland, D. J., Hinterberger, T., Birbaumer, N., & Wolpaw, J. R. (2004).
BCI2000: A general-purpose brain-computer interface (BCI) system. *IEEE Transactions on
Biomedical Engineering, 51*(6), 1034–1043. Distributed by PhysioNet (Goldberger et al.,
2000) under the Open Data Commons Attribution License v1.0.
