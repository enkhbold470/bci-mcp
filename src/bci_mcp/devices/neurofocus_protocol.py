"""NeuroFocus v4 wire protocol — pure decode helpers (no I/O)."""
from __future__ import annotations

import struct

import numpy as np

SERVICE_UUID = "0338ff7c-6251-4029-a5d5-24e4fa856c8d"
DATA_CHAR_UUID = "ad615f2b-cc93-4155-9e4d-f5f32cb9a2d7"
CMD_CHAR_UUID = "b5e3d1c9-8a2f-4e7b-9c6d-1a3f5e7b9c2d"

CMD_START = b"b"
CMD_STOP = b"s"
CMD_RESET = b"v"

DEFAULT_SAMPLE_RATE = 600.0
ADC_LSB_UV = 3.3 / 8_388_608 * 1e6  # ≈0.3933 µV/count at the ADC input
AMP_GAIN = 100.0  # AD8422 instrumentation amplifier
_BINARY_MAGIC = b"\xe7\x1e"


def counts_to_uv(counts):
    """Convert raw 24-bit ADC counts to scalp-referred microvolts."""
    return np.asarray(counts) * (ADC_LSB_UV / AMP_GAIN) if np.ndim(counts) else (
        counts * (ADC_LSB_UV / AMP_GAIN)
    )


def parse_frame(payload: bytes) -> list[int]:
    """Decode one BLE/serial payload into a list of raw ADC counts.

    Supports binary-batch frames (0xE7 0x1E magic) and ASCII decimal frames.
    Returns [] for blank/unparseable ASCII.
    """
    if payload[:2] == _BINARY_MAGIC:
        n = payload[4]
        offset = 5
        out: list[int] = []
        for i in range(n):
            (value,) = struct.unpack_from("<i", payload, offset + i * 4)
            out.append(value)
        return out
    text = payload.decode("utf-8", errors="ignore").strip()
    if not text:
        return []
    try:
        return [int(text)]
    except ValueError:
        return []
