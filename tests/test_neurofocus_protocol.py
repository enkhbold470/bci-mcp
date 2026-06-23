import struct

import numpy as np
import pytest

from bci_mcp.devices import neurofocus_protocol as nf


def test_counts_to_uv_scalp_referred():
    # 1 count → LSB/gain microvolts; ~0.003933 µV
    assert nf.counts_to_uv(1) == pytest.approx(3.3 / 8_388_608 * 1e6 / 100.0, rel=1e-6)
    assert nf.counts_to_uv(0) == 0.0


def test_parse_ascii_frame():
    assert nf.parse_frame(b"12345") == [12345]
    assert nf.parse_frame(b"-678\n") == [-678]


def test_parse_ascii_ignores_blank():
    assert nf.parse_frame(b"   ") == []


def test_parse_binary_batch_frame():
    samples = [1, -2, 3, 4, -5, 6, 7, -8]
    payload = b"\xe7\x1e" + struct.pack("<H", 42) + struct.pack("<B", len(samples))
    payload += b"".join(struct.pack("<i", s) for s in samples)
    assert nf.parse_frame(payload) == samples


def test_uuids_present():
    assert nf.SERVICE_UUID == "0338ff7c-6251-4029-a5d5-24e4fa856c8d"
    assert nf.DATA_CHAR_UUID == "ad615f2b-cc93-4155-9e4d-f5f32cb9a2d7"
    assert nf.CMD_CHAR_UUID == "b5e3d1c9-8a2f-4e7b-9c6d-1a3f5e7b9c2d"


def test_counts_array_to_uv_chunk():
    counts = np.array([0, 1000, -1000], dtype=np.int64)
    uv = nf.counts_to_uv(counts)
    assert uv.shape == (3,)
    assert uv[0] == 0.0
