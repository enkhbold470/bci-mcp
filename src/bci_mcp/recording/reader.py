"""Load EEG recordings (CSV / npz / EDF) into a uniform Recording object."""
from __future__ import annotations

import json
from dataclasses import dataclass, field

import numpy as np


@dataclass
class Recording:
    data: np.ndarray  # (channels, n_samples), float32
    sample_rate: float
    channel_names: list[str]
    metadata: dict = field(default_factory=dict)


def load_recording(path: str) -> Recording:
    ext = path.rsplit(".", 1)[-1].lower()
    if ext == "npz":
        npz = np.load(path, allow_pickle=False)
        meta = json.loads(str(npz["metadata"])) if "metadata" in npz else {}
        return Recording(
            data=npz["data"].astype(np.float32),
            sample_rate=float(npz["sample_rate"]),
            channel_names=[str(c) for c in npz["channel_names"]],
            metadata=meta,
        )
    if ext == "csv":
        import csv

        with open(path, newline="") as f:
            reader = csv.reader(f)
            header = next(reader)
            channel_names = header[1:]  # first col is timestamp
            rows = [[float(x) for x in row] for row in reader]
        arr = np.array(rows, dtype=np.float32).T  # (cols, n)
        sample_rate = 0.0
        if arr.shape[1] > 1:
            dt = arr[0, 1] - arr[0, 0]
            sample_rate = 1.0 / dt if dt > 0 else 0.0
        return Recording(data=arr[1:, :], sample_rate=sample_rate,
                         channel_names=channel_names)
    if ext == "edf":
        import pyedflib

        reader = pyedflib.EdfReader(path)
        n = reader.signals_in_file
        names = [reader.getLabel(i) for i in range(n)]
        rate = reader.getSampleFrequency(0)
        data = np.vstack([reader.readSignal(i) for i in range(n)]).astype(np.float32)
        reader.close()
        return Recording(data=data, sample_rate=float(rate), channel_names=names)
    raise ValueError(f"Unsupported recording format: .{ext}")
