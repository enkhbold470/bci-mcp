import numpy as np
import pytest

from bci_mcp.recording.reader import load_recording
from bci_mcp.recording.writer import save_recording


@pytest.mark.parametrize("ext", ["npz", "csv"])
def test_roundtrip_npz_csv(tmp_path, ext):
    data = np.arange(12, dtype=np.float32).reshape(2, 6)
    path = str(tmp_path / f"rec.{ext}")
    out = save_recording(data, sample_rate=128.0, channel_names=["a", "b"], path=path,
                         metadata={"device": "synthetic"})
    rec = load_recording(out)
    assert rec.sample_rate == 128.0
    assert rec.channel_names == ["a", "b"]
    assert rec.data.shape == (2, 6)
    assert np.allclose(rec.data, data, atol=1e-4)


def test_format_inferred_from_extension(tmp_path):
    data = np.zeros((1, 4), dtype=np.float32)
    out = save_recording(data, 100.0, ["x"], str(tmp_path / "r.npz"))
    assert out.endswith(".npz")


def test_edf_roundtrip(tmp_path):
    pytest.importorskip("pyedflib")
    data = (np.random.default_rng(0).normal(0, 20, (2, 512))).astype(np.float32)
    path = str(tmp_path / "rec.edf")
    save_recording(data, 256.0, ["c3", "c4"], path)
    rec = load_recording(path)
    assert rec.data.shape[0] == 2
    assert rec.sample_rate == 256.0
    # EDF stores with finite precision; check correlation not exact equality
    assert np.corrcoef(rec.data[0], data[0])[0, 1] > 0.99
