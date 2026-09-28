"""Real-EEG check: does the pipeline recover the Berger effect?

Closing the eyes raises posterior alpha power (Berger, 1929) — the most robust
effect in human EEG, so a correct alpha-based pipeline must show it. We use the
PhysioNet EEG Motor Movement/Imagery Dataset (Schalk et al., 2004; Goldberger
et al., 2000): for each of 109 subjects, run R01 is a 1-minute eyes-open
baseline and R02 a 1-minute eyes-closed baseline (64 ch, 160 Hz, BCI2000).

Method (fixed before looking at results): take O1, Oz, O2; cut each run into
non-overlapping 2 s windows; run the unmodified ``Pipeline.current_state()``
(60 Hz notch, 1-45 Hz bandpass, Welch band power, uncalibrated default
scaling) on each window; average per subject. Primary outcome: the ``calm``
metric (α/(α+β)). Secondary: ``meditation``, relative alpha, ``focus``.
Paired Wilcoxon signed-rank across subjects, plus window-level AUC for
separating eyes-closed from eyes-open windows (pooled and within-subject).

Download the 218 EDF files first (see paper/README.md) and pass the directory.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pyedflib
from _common import save
from _windows import state_for
from scipy.stats import mannwhitneyu, wilcoxon

CHANNELS = ("O1", "Oz", "O2")
WIN_S = 2.0
OUTCOMES = ("calm", "meditation", "rel_alpha", "focus")


def load(path: Path) -> tuple[np.ndarray, float]:
    with pyedflib.EdfReader(str(path)) as f:
        labels = [lab.strip(". ").lower() for lab in f.getSignalLabels()]
        idx = [labels.index(c.lower()) for c in CHANNELS]
        fs = float(f.getSampleFrequency(idx[0]))
        data = np.vstack([f.readSignal(i) for i in idx])  # physical units, µV
    return data, fs


def windows(path: Path) -> list[dict]:
    data, fs = load(path)
    n = int(WIN_S * fs)
    out = []
    for start in range(0, data.shape[1] - n + 1, n):
        s = state_for(data[:, start:start + n], fs, notch=60.0)
        out.append({"calm": s.metrics["calm"], "meditation": s.metrics["meditation"],
                    "focus": s.metrics["focus"],
                    "rel_alpha": s.relative_band_powers["alpha"],
                    "status": s.status, "artifacts": s.artifacts, "fs": fs})
    return out


def auc(pos, neg) -> float:
    return float(mannwhitneyu(pos, neg).statistic / (len(pos) * len(neg)))


def bootstrap_ci(diff: np.ndarray, reps: int = 10_000, seed: int = 0) -> list[float]:
    rng = np.random.default_rng(seed)
    meds = [np.median(rng.choice(diff, diff.size)) for _ in range(reps)]
    return [float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5))]


def main(root: Path) -> None:
    subjects, skipped = [], []
    pooled = {o: {"eo": [], "ec": []} for o in OUTCOMES}
    within_auc = []
    status_counts = {"windows": 0, "unreliable": 0, "artifact_windows": 0}
    fs_seen = set()
    for sid in range(1, 110):
        eo_p, ec_p = root / f"S{sid:03d}R01.edf", root / f"S{sid:03d}R02.edf"
        if not (eo_p.exists() and ec_p.exists()):
            skipped.append({"subject": sid, "reason": "file missing"})
            continue
        try:
            eo, ec = windows(eo_p), windows(ec_p)
        except Exception as exc:  # malformed file / missing channel
            skipped.append({"subject": sid, "reason": str(exc)})
            continue
        row = {"subject": sid, "n_eo": len(eo), "n_ec": len(ec)}
        for o in OUTCOMES:
            a, b = [w[o] for w in eo], [w[o] for w in ec]
            row[f"{o}_eo"], row[f"{o}_ec"] = float(np.mean(a)), float(np.mean(b))
            pooled[o]["eo"] += a
            pooled[o]["ec"] += b
        within_auc.append(auc([w["calm"] for w in ec], [w["calm"] for w in eo]))
        for cond, ws in (("eo", eo), ("ec", ec)):
            for w in ws:
                key = f"{cond}_windows_flagged_blink"
                status_counts[key] = status_counts.get(key, 0) + ("blink" in w["artifacts"])
                status_counts[f"{cond}_windows"] = status_counts.get(f"{cond}_windows", 0) + 1
        for w in eo + ec:
            status_counts["windows"] += 1
            status_counts["unreliable"] += w["status"] == "unreliable"
            status_counts["artifact_windows"] += bool(w["artifacts"])
            for a in w["artifacts"]:
                status_counts[f"flag_{a}"] = status_counts.get(f"flag_{a}", 0) + 1
            fs_seen.add(w["fs"])
        subjects.append(row)

    n = len(subjects)
    stats = {}
    for o in OUTCOMES:
        eo = np.array([r[f"{o}_eo"] for r in subjects])
        ec = np.array([r[f"{o}_ec"] for r in subjects])
        diff = ec - eo
        w = wilcoxon(ec, eo)
        # matched-pairs rank-biserial correlation
        ranks = np.argsort(np.argsort(np.abs(diff))) + 1
        rbc = float((ranks[diff > 0].sum() - ranks[diff < 0].sum()) / ranks.sum())
        stats[o] = {
            "median_eo": float(np.median(eo)), "median_ec": float(np.median(ec)),
            "median_diff_ec_minus_eo": float(np.median(diff)),
            "median_diff_95ci": bootstrap_ci(diff),
            "subjects_ec_gt_eo": int((diff > 0).sum()),
            "wilcoxon_W": float(w.statistic), "p_value": float(w.pvalue),
            "rank_biserial": rbc,
            "pooled_window_auc_ec_vs_eo": auc(pooled[o]["ec"], pooled[o]["eo"]),
        }
        print(f"{o:10s} EC>EO in {stats[o]['subjects_ec_gt_eo']}/{n}  "
              f"median {stats[o]['median_eo']:.3f}→{stats[o]['median_ec']:.3f}  "
              f"p={stats[o]['p_value']:.2g}  r={rbc:.2f}  "
              f"AUC={stats[o]['pooled_window_auc_ec_vs_eo']:.3f}")
    wa = np.array(within_auc)
    print(f"within-subject calm AUC median {np.median(wa):.3f}; "
          f"subjects AUC>0.5: {(wa > 0.5).sum()}/{n}")
    print("skipped:", skipped, "fs:", sorted(fs_seen), status_counts)
    save("eyes_closed", {
        "dataset": "PhysioNet EEG Motor Movement/Imagery Dataset v1.0.0, runs R01 "
                   "(eyes open) and R02 (eyes closed)",
        "channels": list(CHANNELS), "window_seconds": WIN_S, "notch_hz": 60.0,
        "calibrated": False, "subjects_analyzed": n, "skipped": skipped,
        "sample_rates_seen": sorted(fs_seen), "window_status": status_counts,
        "primary_outcome": "calm", "outcomes": stats,
        "within_subject_calm_auc": {
            "median": float(np.median(wa)), "q1": float(np.percentile(wa, 25)),
            "q3": float(np.percentile(wa, 75)), "subjects_above_0_5": int((wa > 0.5).sum()),
        },
        "per_subject": subjects,
    })


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "data"))
