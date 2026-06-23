"""Save EEG data to CSV / npz / EDF."""
from __future__ import annotations

import json

import numpy as np


def save_recording(data: np.ndarray, sample_rate: float, channel_names: list[str],
                   path: str, fmt: str | None = None, metadata: dict | None = None) -> str:
    fmt = (fmt or path.rsplit(".", 1)[-1]).lower()
    metadata = metadata or {}
    if fmt == "npz":
        np.savez(path, data=data.astype(np.float32), sample_rate=float(sample_rate),
                 channel_names=np.array(channel_names), metadata=json.dumps(metadata))
    elif fmt == "csv":
        import csv

        n = data.shape[1]
        t = np.arange(n) / sample_rate if sample_rate else np.arange(n, dtype=float)
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", *channel_names])
            for i in range(n):
                writer.writerow([t[i], *data[:, i].tolist()])
    elif fmt == "edf":
        import pyedflib

        n_ch = data.shape[0]
        writer = pyedflib.EdfWriter(path, n_ch, file_type=pyedflib.FILETYPE_EDFPLUS)
        headers = []
        for i in range(n_ch):
            ch = data[i]
            headers.append({
                "label": channel_names[i], "dimension": "uV",
                "sample_frequency": float(sample_rate),
                "physical_min": float(min(ch.min(), -1.0)),
                "physical_max": float(max(ch.max(), 1.0)),
                "digital_min": -32768, "digital_max": 32767,
                "transducer": "", "prefilter": "",
            })
        writer.setSignalHeaders(headers)
        writer.writeSamples([data[i].astype(np.float64) for i in range(n_ch)])
        writer.close()
    else:
        raise ValueError(f"Unsupported recording format: {fmt}")
    return path
