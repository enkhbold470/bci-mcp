from typer.testing import CliRunner

from bci_mcp.cli import app

runner = CliRunner()


def test_record_and_play(tmp_path):
    path = str(tmp_path / "rec.npz")
    r1 = runner.invoke(app, ["record", "--device", "synthetic://?seed=1",
                             "--seconds", "0.4", "--out", path])
    assert r1.exit_code == 0
    r2 = runner.invoke(app, ["play", path, "--once"])
    assert r2.exit_code == 0
    assert "focus" in r2.stdout.lower()
