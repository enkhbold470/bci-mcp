"""Render the paper figures from paper/results/*.json."""
from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from _common import RESULTS  # noqa: E402

FIG = RESULTS.parent / "figures"
plt.rcParams.update({"font.size": 9, "font.family": "serif", "figure.dpi": 150})


def load(name: str) -> dict:
    return json.loads((RESULTS / f"{name}.json").read_text())


def eyes_closed() -> None:
    d = load("eyes_closed")
    subj = d["per_subject"]
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.8))
    for ax, key, label in [(axes[0], "calm", "calm  (α/(α+β), scaled)"),
                           (axes[1], "rel_alpha", "relative alpha power")]:
        eo = np.array([s[f"{key}_eo"] for s in subj])
        ec = np.array([s[f"{key}_ec"] for s in subj])
        for a, b in zip(eo, ec, strict=True):
            ax.plot([0, 1], [a, b], color="0.3" if b > a else "tab:red",
                    alpha=0.25, lw=0.7)
        ax.boxplot([eo, ec], positions=[0, 1], widths=0.35, showfliers=False)
        ax.set_xticks([0, 1], ["eyes open", "eyes closed"])
        ax.set_ylabel(label)
        n_up = int((ec > eo).sum())
        ax.set_title(f"EC > EO in {n_up}/{len(eo)} subjects", fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG / "eyes_closed.pdf")
    fig.savefig(FIG / "eyes_closed.png")


def artifacts() -> None:
    d = load("artifacts")
    fig, ax = plt.subplots(figsize=(3.2, 2.5))
    for name, marker in [("blink", "o"), ("emg", "s"), ("railing", "^")]:
        rows = [r for r in d["injected"] if r["artifact"] == name]
        ax.plot([r["amplitude_uv"] for r in rows], [r["flag_rate"] for r in rows],
                marker=marker, label=name, lw=1)
    ax.set_xscale("log")
    ax.set_xlabel("injected amplitude (µV)")
    ax.set_ylabel("flag rate")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / "artifacts.pdf")


def sweep() -> None:
    d = load("synthetic_sweep")
    x = [r["focus_param"] for r in d["levels"]]
    fig, ax = plt.subplots(figsize=(3.2, 2.5))
    for m in ("focus", "calm", "fatigue"):
        ax.errorbar(x, [r[f"{m}_mean"] for r in d["levels"]],
                    yerr=[r[f"{m}_sd"] for r in d["levels"]], label=m, capsize=2, lw=1)
    ax.set_xlabel("synthetic generator 'focus' parameter")
    ax.set_ylabel("metric (uncalibrated, 0–1)")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / "synthetic_sweep.pdf")


if __name__ == "__main__":
    FIG.mkdir(exist_ok=True)
    for fn in (sweep, artifacts, eyes_closed):
        try:
            fn()
            print("ok", fn.__name__)
        except FileNotFoundError as exc:
            print("skip", fn.__name__, exc)
